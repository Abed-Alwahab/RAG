
from collections import Counter

from langchain_text_splitters import RecursiveCharacterTextSplitter
from ingest import load_pdfs


# ==========================================
# CONFIGURATION
# ==========================================

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


# ==========================================
# CREATE CHUNKS
# ==========================================

def create_chunks():
    documents = load_pdfs()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            "،",
            " ",
            ""
        ]
    )

    chunks = []

    for doc in documents:
        text = doc["text"].strip()

        if not text:
            continue

        pieces = splitter.split_text(text)

        for index, piece in enumerate(pieces):
            piece = piece.strip()

            if not piece:
                continue

            chunks.append({
                "text": piece,
                "source": doc["source"],
                "page": int(doc["page"]),
                "chunk_id": index,
                "method": doc.get("method", "unknown")
            })

    return chunks


# ==========================================
# TEST
# ==========================================

if __name__ == "__main__":
    chunks = create_chunks()

    print("\n" + "=" * 50)
    print("CHUNKING RESULTS")
    print("=" * 50)

    print(f"Total chunks: {len(chunks)}")

    counts = Counter(
        chunk["source"]
        for chunk in chunks
    )

    for source, count in sorted(counts.items()):
        print(f"{source}: {count} chunks")

    print("=" * 50)
