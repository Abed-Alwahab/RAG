
import re
from collections import defaultdict
from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer


DB_PATH = "./vectorstore_v3"
COLLECTION_NAME = "aaup_documents"

EMBEDDING_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

TOP_K = 30
MAX_PAGES = 6

model = SentenceTransformer(EMBEDDING_MODEL)

client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_collection(name=COLLECTION_NAME)


# Arabic normalization
def normalize(text):
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    text = re.sub(r"[إأآٱ]", "ا", text)
    text = text.replace("ى", "ي")
    text = text.replace("ـ", "")
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


STOP_WORDS = {
    "ما", "هو", "هي", "كم", "هل", "في", "من",
    "على", "عن", "الى", "يمكن", "عدد",
    "التي", "الذي", "شو", "بدي", "بقدر",
    "متى", "وما", "وكم", "هذه", "هذا",
    "الجامعة", "العربية", "الامريكية"
}


def stem_word(word):
    word = normalize(word)

    # Handle common Arabic attached prefixes.
    for prefix in ("وال", "بال", "لل", "ال"):
        if word.startswith(prefix) and len(word) > len(prefix) + 2:
            word = word[len(prefix):]
            break

    # Handle possessive suffixes.
    for suffix in ("تنا", "نا", "ها", "هم"):
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            word = word[:-len(suffix)]
            break

    # Normalize common feminine endings.
    if word.endswith("ة"):
        word = word[:-1]

    return word


def tokenize(text):
    words = re.findall(
        r"[\u0621-\u064A]+|\d+",
        normalize(text)
    )

    tokens = []

    for word in words:
        stem = stem_word(word)

        if len(stem) >= 2 and stem not in STOP_WORDS:
            tokens.append(stem)

    return tokens


@lru_cache(maxsize=1)
def load_all_chunks():
    return collection.get(
        include=["documents", "metadatas"]
    )


def keyword_score(question, text):
    query_tokens = set(tokenize(question))

    if not query_tokens:
        return 0.0

    document_tokens = set(tokenize(text))

    matches = query_tokens.intersection(document_tokens)

    score = len(matches) / len(query_tokens)

    # Extra reward for matching important words
    # near the beginning of a line.
    lines = text.splitlines()

    for line in lines:
        line_tokens = set(tokenize(line))

        if not line_tokens:
            continue

        overlap = query_tokens.intersection(line_tokens)

        if overlap:
            short_line = len(line.strip()) <= 100

            if short_line:
                score += 0.15 * (
                    len(overlap) / len(query_tokens)
                )

    return score

def heading_bonus(question, page_text):
    query = normalize(question)

    heading_patterns = {
        "رؤي": ["رؤيتنا:", "رؤيتنا", "الرؤية:"],
        "رسال": ["رسالتنا:", "رسالتنا", "الرسالة:"],
        "مراكز": ["مراكز الجامعة:"],
        "مكتب": ["المكتبة:", "المكتبة"],
    }

    question_tokens = set(tokenize(question))

    for keyword, headings in heading_patterns.items():
        if any(keyword in token for token in question_tokens):
            for heading in headings:
                if normalize(heading) in normalize(page_text):
                    return 0.02

    return 0.0


def retrieve_documents(
    question,
    top_k=TOP_K,
    max_pages=MAX_PAGES
):
    total = collection.count()

    if total == 0:
        return []

    data = load_all_chunks()

    # 1. Semantic search
    embedding = model.encode(
        question,
        normalize_embeddings=True
    ).tolist()

    semantic_results = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k, total),
        include=["documents", "metadatas", "distances"]
    )

    semantic_ids = semantic_results["ids"][0]

    # 2. Keyword search
    lexical_scores = []

    for chunk_id, text in zip(
        data["ids"],
        data["documents"]
    ):
        score = keyword_score(question, text)

        if score > 0:
            lexical_scores.append((chunk_id, score))

    lexical_scores.sort(
        key=lambda item: item[1],
        reverse=True
    )

    lexical_ids = [
        item[0]
        for item in lexical_scores[:top_k]
    ]

    # 3. RRF ranking
    chunk_scores = defaultdict(float)

    for rank, chunk_id in enumerate(
        semantic_ids, start=1
    ):
        chunk_scores[chunk_id] += 1 / (60 + rank)

    for rank, chunk_id in enumerate(
        lexical_ids, start=1
    ):
        chunk_scores[chunk_id] += 1.5 / (60 + rank)

    # 4. Group all chunks by source and page
    pages = defaultdict(list)
    page_scores = defaultdict(float)

    for chunk_id, text, metadata in zip(
        data["ids"],
        data["documents"],
        data["metadatas"]
    ):
        key = (
            metadata["source"],
            int(metadata["page"])
        )

        pages[key].append((
            int(metadata["chunk_id"]),
            text
        ))

        if chunk_id in chunk_scores:
            # Use the best chunk score per page,
            # rather than summing every chunk.
            page_scores[key] = max(
                page_scores[key],
                chunk_scores[chunk_id]
            )

    # 5. Rank pages
    ranked_pages = sorted(
    page_scores,
    key=lambda key: (
        page_scores[key]
        + heading_bonus(
            question,
            "\n".join(
                text for _, text in pages[key]
            )
        )
    ),
    reverse=True
)

    results = []

    for key in ranked_pages[:max_pages]:
        source, page_number = key

        page_chunks = sorted(
            pages[key],
            key=lambda item: item[0]
        )

        page_text = "\n\n".join(
            text for _, text in page_chunks
        )

        results.append({
            "source": source,
            "page": page_number,
            "text": page_text,
            "score": page_scores[key]
        })

    return results


if __name__ == "__main__":
    print("AAUP Hybrid Search")
    print("Indexed chunks:", collection.count())

    while True:
        question = input(
            "\nاسأل سؤالك (exit للخروج): "
        ).strip()

        if question.lower() == "exit":
            break

        results = retrieve_documents(question)

        print(f"\nRetrieved {len(results)} pages")

        for rank, result in enumerate(results, start=1):
            print("\n" + "=" * 55)
            print("Rank:", rank)
            print("Source:", result["source"])
            print("Page:", result["page"])
            print("Score:", round(result["score"], 5))
            print("Text:", result["text"][:500])
