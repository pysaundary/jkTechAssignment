import os
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

from src.models.models import UserFileEmbedding
import src.constant as constants
import asyncio

class Bumblebee:
    def __init__(self,**kwargs):
        self.folderPath = kwargs.get("folder_path")
        self.topicUuid = kwargs.get("topic_uuid")
        self.modelName = kwargs.get("model_name","BAAI/bge-small-en-v1.5")
        self.device = kwargs.get("device","cpu")
        self.normalizeEmbeddings = kwargs.get("normalize_embeddings",True)
        self.chunkSize = kwargs.get("chunk_size",700) 
        self.chunkOverlap = kwargs.get("chunk_overlap",50)
        self.logger  = constants.internalLoggers.get("transformer_logs",None)
        self.logger.info(f"Bumblebee called for {self.topicUuid}")
    
    async def store_embeddings(self,docs_after_split, embeddings):
        try:
            self.logger.info(f"storing data into embedding models for {self.topicUuid}")
            for doc, embedding in zip(docs_after_split, embeddings):
                await UserFileEmbedding.create(
                    topic_uuid=self.topicUuid,
                    embedding=embedding.tolist(),  # Convert numpy array to list for JSON storage
                )
            self.logger.info(f"store topic uuid {self.topicUuid} success")
        except Exception as e:
            self.logger.error(f"store file embedding failed , uuid {self.topicUuid}")

    async def createVector(self):
        try:
            self.logger.info(f"creating embedding {self.topicUuid}")
            loader = PyPDFDirectoryLoader(self.folderPath)
            docs_before_split = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunkSize, chunk_overlap=self.chunkOverlap)
            docs_after_split = text_splitter.split_documents(docs_before_split)
            # Compute average document length (optional metrics)
            avg_doc_length = lambda docs: sum([len(doc.page_content) for doc in docs]) // len(docs)
            avg_char_before_split = avg_doc_length(docs_before_split)
            avg_char_after_split = avg_doc_length(docs_after_split)
            self.logger.info(f"avg char before split {avg_char_before_split} and avg char after split {avg_char_after_split} for {self.topicUuid}")
            # Initialize embeddings model
            huggingface_embeddings = HuggingFaceBgeEmbeddings(
                model_name=self.modelName,
                model_kwargs={"device": self.device},
                encode_kwargs={"normalize_embeddings": self.normalizeEmbeddings},
            )
            self.logger.info(f"Initialize embeddings model {self.topicUuid}")
            # Generate embeddings
            embeddings : list = []
            for doc in docs_after_split:
                embeddings.append(np.array(huggingface_embeddings.embed_query(doc.page_content)))
                await asyncio.sleep(.15)

            self.logger.info(f"Generate embeddings {self.topicUuid}")
            # Store embeddings in the database
            
            await self.store_embeddings(docs_after_split, embeddings)
            self.logger.info(f"Stored embeddings under topic UUID: {self.topicUuid}")
        except Exception as e:
            self.logger.error(f"failed to create embedding {self.topicUuid} : due to {e}")