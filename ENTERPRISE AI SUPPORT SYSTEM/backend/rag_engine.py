import os

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(__file__)

POLICY_FILE = os.path.join(
    BASE_DIR,
    "company_policy.txt"
)

INDEX_PATH = os.path.join(
    BASE_DIR,
    "faiss_index"
)

DOCUMENTS_DIR = os.path.join(
    BASE_DIR,
    "..",
    "data",
    "documents"
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

def get_embeddings():

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


# ============================================================
# BUILD FAISS KNOWLEDGE BASE
# ============================================================

def build_vector_store():

    documents = []


    # --------------------------------------------------------
    # Load existing company policy
    # --------------------------------------------------------

    if os.path.exists(POLICY_FILE):

        loader = TextLoader(
            POLICY_FILE,
            encoding="utf-8"
        )

        documents.extend(
            loader.load()
        )


    # --------------------------------------------------------
    # Load all PDF documents
    # --------------------------------------------------------

    if os.path.exists(DOCUMENTS_DIR):

        pdf_files = sorted(
            filename
            for filename in os.listdir(DOCUMENTS_DIR)
            if filename.lower().endswith(".pdf")
        )

        for filename in pdf_files:

            pdf_path = os.path.join(
                DOCUMENTS_DIR,
                filename
            )

            try:

                loader = PyPDFLoader(
                    pdf_path
                )

                pdf_documents = loader.load()

                documents.extend(
                    pdf_documents
                )

                print(
                    f"Loaded: {filename} "
                    f"({len(pdf_documents)} pages)"
                )

            except Exception as e:

                print(
                    f"Warning: Could not load "
                    f"{filename}: {e}"
                )


    # --------------------------------------------------------
    # Validate documents
    # --------------------------------------------------------

    if not documents:

        raise ValueError(
            "No knowledge-base documents found."
        )


    print(
        f"\nTotal pages/documents loaded: "
        f"{len(documents)}"
    )


    # ========================================================
    # SPLIT DOCUMENTS INTO CHUNKS
    # ========================================================

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    docs = text_splitter.split_documents(
        documents
    )


    print(
        f"Total chunks created: {len(docs)}"
    )


    # ========================================================
    # CREATE EMBEDDINGS
    # ========================================================

    embeddings = get_embeddings()


    # ========================================================
    # CREATE FAISS VECTOR DATABASE
    # ========================================================

    vector_db = FAISS.from_documents(
        docs,
        embeddings
    )


    # ========================================================
    # SAVE FAISS INDEX
    # ========================================================

    vector_db.save_local(
        INDEX_PATH
    )


    print(
        "\nFAISS knowledge base updated successfully!"
    )


# ============================================================
# QUERY RAG
# ============================================================

def query_rag(query_text: str):

    if not query_text or not query_text.strip():

        return []


    embeddings = get_embeddings()


    # --------------------------------------------------------
    # Load existing FAISS index
    # --------------------------------------------------------

    vector_db = FAISS.load_local(
        INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )


    # --------------------------------------------------------
    # Retrieve top 5 relevant chunks
    # --------------------------------------------------------

    results = vector_db.similarity_search(
        query_text,
        k=5
    )


    return [
        doc.page_content
        for doc in results
    ]


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    build_vector_store()