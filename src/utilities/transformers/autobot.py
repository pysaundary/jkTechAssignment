import os
import json
import hashlib
from pathlib import Path
from urllib.request import urlretrieve
import numpy as np
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.llms import HuggingFacePipeline
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document

from src.models.models import UserFileEmbedding
import src.constant as constants
import asyncio

class Bumblebee:
    def __init__(self,**kwargs):
        self.folderPath = kwargs.get("folder_path",None)
        self.topicUuid = kwargs.get("topic_uuid",None)
        self.modelName = kwargs.get("model_name","BAAI/bge-small-en-v1.5")
        self.device = kwargs.get("device","cpu")
        self.normalizeEmbeddings = kwargs.get("normalize_embeddings",True)
        self.chunkSize = kwargs.get("chunk_size",700) 
        self.chunkOverlap = kwargs.get("chunk_overlap",50)
        self.logger  = constants.internalLoggers.get("transformer_logs",None)
        self.logger.info(f"Bumblebee called for {self.topicUuid}")
    
    async def store_embeddings(self):
        try:
            await UserFileEmbedding.create(
                    topic_uuid=self.topicUuid,
                    folder_name=self.folderPath,  # Convert numpy array to list for JSON storage
                )
            self.logger.info(f"store topic uuid {self.topicUuid} success")
        except Exception as e:
            self.logger.error(f"store file embedding failed , uuid {self.topicUuid}")

    async def createAndCheckAnswer(self, query: str):
        try:
            embeddings_path = Path(self.folderPath) / f"{self.topicUuid}_embeddings"
            metadata_path = embeddings_path.with_suffix(".meta.json")

            if embeddings_path.exists() and metadata_path.exists():
                self.logger.info(f"Loading cached embeddings for {self.topicUuid}")
                
                # Load metadata
                with open(metadata_path, 'r') as f:
                    data = json.load(f)
                docs_after_split = [Document(**doc) for doc in data["documents"]]

                # Load vectorstore
                huggingface_embeddings = HuggingFaceBgeEmbeddings(
                    model_name=self.modelName,
                    model_kwargs={"device": self.device},
                    encode_kwargs={"normalize_embeddings": self.normalizeEmbeddings},
                )
                # vectorstore = FAISS.load_local(str(embeddings_path), huggingface_embeddings)
                vectorstore = FAISS.load_local(str(embeddings_path), huggingface_embeddings, allow_dangerous_deserialization=True)
            else:
                self.logger.info(f"Creating embeddings for {self.topicUuid}")
                
                loader = PyPDFDirectoryLoader(self.folderPath)
                docs_before_split = loader.load()
                folder_hash = self._compute_folder_hash(self.folderPath)

                text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunkSize, chunk_overlap=self.chunkOverlap)
                docs_after_split = text_splitter.split_documents(docs_before_split)

                # Initialize embeddings model
                huggingface_embeddings = HuggingFaceBgeEmbeddings(
                    model_name=self.modelName,
                    model_kwargs={"device": self.device},
                    encode_kwargs={"normalize_embeddings": self.normalizeEmbeddings},
                )

                # Generate embeddings and vectorstore
                vectorstore = FAISS.from_documents(docs_after_split, huggingface_embeddings)
                vectorstore.save_local(str(embeddings_path))

                # Save metadata
                serialized_docs = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs_after_split]
                with open(metadata_path, 'w') as f:
                    json.dump({"documents": serialized_docs, "hash": folder_hash}, f)

            relevant_documents = vectorstore.similarity_search(query)
            ans = {i: a.page_content for i, a in enumerate(relevant_documents)}
            self.logger.info(f"Answer generated for {self.topicUuid}")
            return ans
        except Exception as e:
            self.logger.error(f"Failed to create embedding {self.topicUuid}: {e}")
            return {"failed": f"Failed to create embedding {self.topicUuid}: {e}"}

    def _compute_folder_hash(self, folder_path):
        """Compute a hash of the folder's content for change tracking."""
        hasher = hashlib.sha256()
        for root, _, files in os.walk(folder_path):
            for file in sorted(files):
                filepath = os.path.join(root, file)
                hasher.update(file.encode())
                with open(filepath, 'rb') as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)
        return hasher.hexdigest()