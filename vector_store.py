
import shutil
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from chunking import create_chunks

DB_PATH = Path("./vectorstore_v3")
COLLECTION_NAME = "aaup_documents"

EMBEDDING_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def build_vector_store():
    chunks = create_chunks()

    if not chunks:
        raise RuntimeError("No chunks found. Database not changed.")

    print(f"\nPreparing {len(chunks)} chunks...")

    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=True
    ).tolist()

    ids = [
        f"doc_{index}"
        for index in range(len(chunks))
    ]

    metadatas = [
        {
            "source": chunk["source"],
            "page": chunk["page"],
            "chunk_id": chunk["chunk_id"],
            "method": chunk["method"]
        }
        for chunk in chunks
    ]

    # Use a temporary database so failed builds
    # do not damage the existing database.
    temp_path = DB_PATH

    if temp_path.exists():
        shutil.rmtree(temp_path)

    client = chromadb.PersistentClient(path=str(temp_path))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    batch_size = 100

    for start in range(0, len(chunks), batch_size):
        end = start + batch_size

        collection.add(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
            embeddings=embeddings[start:end]
        )

    count = collection.count()

    if count != len(chunks):
        raise RuntimeError(
            f"Expected {len(chunks)} chunks, found {count}"
        )

    print(f"Verified {count} chunks.")

    # Close references before moving the database.
    del collection
    del client

 

    print("\nVector database built successfully!")
    print("Database:", DB_PATH)
    print("Total chunks:", count)


if __name__ == "__main__":
    build_vector_store()
