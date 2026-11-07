
import re
from pathlib import Path
from collections import defaultdict
from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer


# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "vectorstore_v3"

COLLECTION_NAME = "aaup_documents"

EMBEDDING_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

TOP_K = 30
MAX_PAGES = 6

RRF_K = 60
LEXICAL_WEIGHT = 1.5


# ==========================================
# INITIALIZE SEARCH
# ==========================================

model = SentenceTransformer(EMBEDDING_MODEL)

client = chromadb.PersistentClient(
    path=str(DB_PATH)
)

collection = client.get_collection(
    name=COLLECTION_NAME
)


# ==========================================
# TEXT NORMALIZATION
# ==========================================

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


# ==========================================
# ARABIC STEMMING
# ==========================================

def stem_word(word):
    word = normalize(word)

    # Preserve course codes such as COMP336.
    if re.fullmatch(r"[a-z]+\s*-?\s*\d+", word):
        return re.sub(r"[\s-]+", "", word)

    for prefix in ("وال", "بال", "لل", "ال"):
        if (
            word.startswith(prefix)
            and len(word) > len(prefix) + 2
        ):
            word = word[len(prefix):]
            break

    for suffix in ("تنا", "نا", "ها", "هم"):
        if (
            word.endswith(suffix)
            and len(word) > len(suffix) + 2
        ):
            word = word[:-len(suffix)]
            break

    if word.endswith("ة"):
        word = word[:-1]

    return word


# ==========================================
# TOKENIZATION
# ==========================================

def tokenize(text):
    text = normalize(text)

    # Preserve course codes (COMP336, MATH141, etc.).
    text = re.sub(
        r"\b([a-z]{2,})\s*[-]?\s*(\d+)\b",
        r"\1\2",
        text
    )

    words = re.findall(
        r"[a-z]+\d+|[\u0621-\u064A]+|[a-z]+|\d+",
        text
    )

    tokens = []

    for word in words:
        stem = stem_word(word)

        if (
            len(stem) >= 2
            and stem not in STOP_WORDS
        ):
            tokens.append(stem)

    return tokens


# ==========================================
# LOAD CHUNKS
# ==========================================

@lru_cache(maxsize=1)
def load_all_chunks():
    return collection.get(
        include=["documents", "metadatas"]
    )


# ==========================================
# KEYWORD SEARCH
# ==========================================

def keyword_score(question, text):
    query_tokens = set(tokenize(question))

    if not query_tokens:
        return 0.0

    document_tokens = set(tokenize(text))

    matches = query_tokens.intersection(
        document_tokens
    )

    score = len(matches) / len(query_tokens)

    # Reward short matching lines.
    for line in text.splitlines():
        line_tokens = set(tokenize(line))

        if not line_tokens:
            continue

        overlap = query_tokens.intersection(
            line_tokens
        )

        if overlap and len(line.strip()) <= 100:
            score += 0.15 * (
                len(overlap) / len(query_tokens)
            )

    # Strong bonus for exact course-code matches.
    course_codes = {
        token
        for token in query_tokens
        if re.fullmatch(r"[a-z]+\d+", token)
    }

    if course_codes:
        matched_codes = course_codes.intersection(
            document_tokens
        )

        score += 1.0 * len(matched_codes)

    return score


# ==========================================
# HEADING BONUS
# ==========================================

def heading_bonus(question, page_text):
    heading_patterns = {
        "رؤي": ["رؤيتنا:", "رؤيتنا", "الرؤية:"],
        "رسال": ["رسالتنا:", "رسالتنا", "الرسالة:"],
        "مراكز": ["مراكز الجامعة:"],
        "مكتب": ["المكتبة:", "المكتبة"]
    }

    question_tokens = set(tokenize(question))
    normalized_page = normalize(page_text)

    for keyword, headings in heading_patterns.items():
        if any(
            keyword in token
            for token in question_tokens
        ):
            if any(
                normalize(heading) in normalized_page
                for heading in headings
            ):
                return 0.02

    return 0.0


# ==========================================
# RECONSTRUCT PAGE
# ==========================================

def reconstruct_page(page_chunks):
    page_chunks = sorted(
        page_chunks,
        key=lambda item: item[0]
    )

    if not page_chunks:
        return ""

    result = page_chunks[0][1]

    for _, text in page_chunks[1:]:
        text = text.strip()

        if not text:
            continue

        # Skip exact duplicate chunks.
        if text in result:
            continue

        # Remove repeated overlap between chunks.
        max_overlap = min(
            len(result),
            len(text),
            300
        )

        overlap = 0

        for size in range(max_overlap, 19, -1):
            if result[-size:] == text[:size]:
                overlap = size
                break

        if overlap:
            result += text[overlap:]
        else:
            result += "\n\n" + text

    return result


# ==========================================
# HYBRID RETRIEVAL
# ==========================================

def retrieve_documents(
    question,
    top_k=TOP_K,
    max_pages=MAX_PAGES
):
    question = question.strip()

    if not question:
        return []

    total = collection.count()

    if total == 0:
        return []

    data = load_all_chunks()

    # --------------------------------------
    # 1. SEMANTIC SEARCH
    # --------------------------------------

    embedding = model.encode(
        question,
        normalize_embeddings=True
    ).tolist()

    semantic_results = collection.query(
        query_embeddings=[embedding],
        n_results=min(top_k, total),
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    semantic_ids = semantic_results["ids"][0]

    # --------------------------------------
    # 2. KEYWORD SEARCH
    # --------------------------------------

    lexical_scores = []

    for chunk_id, text in zip(
        data["ids"],
        data["documents"]
    ):
        score = keyword_score(
            question,
            text
        )

        if score > 0:
            lexical_scores.append(
                (chunk_id, score)
            )

    lexical_scores.sort(
        key=lambda item: item[1],
        reverse=True
    )

    lexical_ids = [
        item[0]
        for item in lexical_scores[:top_k]
    ]

    # --------------------------------------
    # 3. RRF RANKING
    # --------------------------------------

    chunk_scores = defaultdict(float)

    for rank, chunk_id in enumerate(
        semantic_ids,
        start=1
    ):
        chunk_scores[chunk_id] += (
            1 / (RRF_K + rank)
        )

    for rank, chunk_id in enumerate(
        lexical_ids,
        start=1
    ):
        chunk_scores[chunk_id] += (
            LEXICAL_WEIGHT / (RRF_K + rank)
        )

    # --------------------------------------
    # 4. GROUP CHUNKS BY PAGE
    # --------------------------------------

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
            page_scores[key] = max(
                page_scores[key],
                chunk_scores[chunk_id]
            )

    # --------------------------------------
    # 5. RANK PAGES
    # --------------------------------------

    ranked_pages = sorted(
        page_scores,
        key=lambda key: (
            page_scores[key]
            + heading_bonus(
                question,
                "\n".join(
                    text
                    for _, text in pages[key]
                )
            )
        ),
        reverse=True
    )

    # --------------------------------------
    # 6. BUILD RESULTS
    # --------------------------------------

    results = []

    for key in ranked_pages[:max_pages]:
        source, page_number = key

        page_text = reconstruct_page(
            pages[key]
        )

        results.append({
            "source": source,
            "page": page_number,
            "text": page_text,
            "score": (
                page_scores[key]
                + heading_bonus(question, page_text)
            )
        })

    return results


# ==========================================
# TERMINAL TEST
# ==========================================

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

        print(
            f"\nRetrieved {len(results)} pages"
        )

        for rank, result in enumerate(
            results,
            start=1
        ):
            print("\n" + "=" * 55)
            print("Rank:", rank)
            print("Source:", result["source"])
            print("Page:", result["page"])
            print(
                "Score:",
                round(result["score"], 5)
            )
            print("Text:", result["text"][:500])
