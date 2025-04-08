import os
import chromadb
from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader


class RAGEngine:
    def __init__(self, doc_dir="documents"):
        """
        Initialize the RAGEngine. This class is responsible for extracting text from documents and storing it in a vector store.

        Args:
            doc_dir (str): The directory where the documents are stored. Defaults to "documents".
        """
        self.doc_dir = doc_dir
        self.embedding_model = OllamaEmbeddings(model="llama3.2:3b")  # ou llama3
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

        if not os.path.exists("./vectorstore"):
            os.makedirs("./vectorstore")

        self.vectordb = None
        self.rebuild_index()

    def _load_documents(self):
        docs = []
        for fname in os.listdir(self.doc_dir):
            path = os.path.join(self.doc_dir, fname)
            if fname.endswith(".pdf"):
                loader = PyPDFLoader(path)
            elif fname.endswith(".txt"):
                loader = TextLoader(path, encoding="utf-8")
            elif fname.endswith(".docx"):
                loader = Docx2txtLoader(path)
            else:
                continue
            docs.extend(loader.load())
        return docs

    def rebuild_index(self):
        docs = self._load_documents()
        if not docs:
            self.vectordb = None
            return
        chunks = self.splitter.split_documents(docs)
        self.vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding_model,
            persist_directory="./vectorstore"
        )
        self.vectordb.persist()

    def retrieve(self, query, k=5):
        if not self.vectordb:
            return []
        results = self.vectordb.similarity_search(query, k=k)
        return [doc.page_content for doc in results]

    def delete_document(self, doc_name):
        """Supprime le fichier et reconstruit l'index."""
        path = os.path.join(self.doc_dir, doc_name)
        if os.path.exists(path):
            os.remove(path)
        self.rebuild_index()
