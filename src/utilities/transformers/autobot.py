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
    
    async def get_answer_from_uuid(self, query, topic_uuid):
        """
        Retrieve the most relevant answer for a given query and topic UUID.

        Args:
            query (str): The user's question.
            topic_uuid (str): The topic UUID to filter embeddings.

        Returns:
            str: The most relevant answer document's content, or None if no relevant documents are found.
        """
        try:
            self.logger.info(f"Fetching embeddings for topic UUID: {topic_uuid}")
            # Fetch all embeddings associated with the given topic UUID from the database
            embedding_records = await UserFileEmbedding.find(UserFileEmbedding.topic_uuid == topic_uuid).to_list()

            if not embedding_records:
                self.logger.warning(f"No embeddings found for topic UUID: {topic_uuid}")
                return "No embeddings found for the provided topic UUID."

            # Extract embeddings and associated metadata
            embeddings = [np.array(record.embedding) for record in embedding_records]
            docs = [record.metadata.get("doc_content", "") for record in embedding_records]

            if not docs:
                self.logger.warning(f"No document contents associated with embeddings for UUID: {topic_uuid}")
                return "No documents found for the provided topic UUID."

            # Generate query embedding using the same embedding model
            huggingface_embeddings = HuggingFaceBgeEmbeddings(
                model_name=self.modelName,
                model_kwargs={"device": self.device},
                encode_kwargs={"normalize_embeddings": self.normalizeEmbeddings},
            )
            query_embedding = np.array(huggingface_embeddings.embed_query(query))

            # Compute cosine similarities between query embedding and stored embeddings
            similarities = [
                np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding))
                for embedding in embeddings
            ]

            # Find the index of the most similar embedding
            most_similar_index = int(np.argmax(similarities))

            # Return the associated document content
            answer = docs[most_similar_index]
            self.logger.info(f"Answer retrieved for query '{query}' under topic UUID: {topic_uuid}")
            return answer

        except Exception as e:
            self.logger.error(f"Failed to retrieve answer for query '{query}' and UUID '{topic_uuid}': {e}")
            return f"Error: {str(e)}"
