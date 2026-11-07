
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ingest import load_pdfs

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def create_chunks():
    documents = load_pdfs()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "،", " ", ""]
    )

    chunks = []

    for doc in documents:
        text = doc["text"].strip()

        if not text:
            continue

        pieces = splitter.split_text(text)

        for index, piece in enumerate(pieces):
            chunks.append({
                "text": piece,
                "source": doc["source"],
                "page": int(doc["page"]),
                "chunk_id": index,
                "method": doc.get("method", "unknown")
            })

    return chunks


if __name__ == "__main__":
    chunks = create_chunks()

    print("Total chunks:", len(chunks))

    sources = sorted(set(c["source"] for c in chunks))

    for source in sources:
        count = sum(c["source"] == source for c in chunks)
        print(f"{source}: {count} chunks")
