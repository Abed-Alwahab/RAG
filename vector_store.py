
import gc
import shutil
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from chunking import create_chunks


# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "vectorstore_v3"
TEMP_PATH = BASE_DIR / "vectorstore_v3_building"
BACKUP_PATH = BASE_DIR / "vectorstore_v3_backup"

COLLECTION_NAME = "aaup_documents"

EMBEDDING_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

BATCH_SIZE = 100


# ==========================================
# BUILD VECTOR DATABASE
# ==========================================

def build_vector_store():

    # STEP 1: LOAD AND CHUNK DOCUMENTS
    print("\n[1/6] Loading and chunking documents...")

    chunks = create_chunks()

    if not chunks:
        raise RuntimeError(
            "No chunks found. Existing database unchanged."
        )

    print(f"Total chunks: {len(chunks)}")

    # STEP 2: GENERATE EMBEDDINGS
    print("\n[2/6] Generating embeddings...")

    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

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

    # STEP 3: PREPARE TEMPORARY DATABASE
    print("\n[3/6] Preparing temporary database...")

    if TEMP_PATH.exists():
        shutil.rmtree(TEMP_PATH)

    client = None
    collection = None

    try:
        client = chromadb.PersistentClient(
            path=str(TEMP_PATH)
        )

        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        # STEP 4: STORE CHUNKS
        print("\n[4/6] Storing chunks...")

        for start in range(0, len(chunks), BATCH_SIZE):
            end = start + BATCH_SIZE

            collection.add(
                ids=ids[start:end],
                documents=texts[start:end],
                metadatas=metadatas[start:end],
                embeddings=embeddings[start:end]
            )

        # STEP 5: VERIFY DATABASE
        print("\n[5/6] Verifying database...")

        count = collection.count()

        if count != len(chunks):
            raise RuntimeError(
                f"Expected {len(chunks)} chunks, found {count}"
            )

        print(f"Verified {count} chunks.")

    finally:
        collection = None
        client = None
        gc.collect()

    # STEP 6: REPLACE OLD DATABASE
    print("\n[6/6] Activating new database...")

    # Do not overwrite an existing backup.
    if BACKUP_PATH.exists():
        raise RuntimeError(
            f"Backup already exists: {BACKUP_PATH}\n"
            "Existing database was not replaced. "
            "Review the backup before retrying."
        )

    old_database_moved = False

    try:
        if DB_PATH.exists():
            DB_PATH.rename(BACKUP_PATH)
            old_database_moved = True

        TEMP_PATH.rename(DB_PATH)

    except Exception:
        # Restore old database if activation failed.
        if (
            old_database_moved
            and not DB_PATH.exists()
            and BACKUP_PATH.exists()
        ):
            BACKUP_PATH.rename(DB_PATH)

        raise

    print("\n" + "=" * 50)
    print("VECTOR DATABASE BUILT SUCCESSFULLY")
    print("=" * 50)
    print("Database:", DB_PATH)
    print("Total chunks:", len(chunks))

    if old_database_moved:
        print("Previous database backup:", BACKUP_PATH)

    print("=" * 50)


if __name__ == "__main__":
    build_vector_store()
