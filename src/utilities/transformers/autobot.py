import traceback
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.llms import HuggingFacePipeline
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS


from src.models.models import UserFileEmbedding,UserFilesModel
import src.constant as constants
import asyncio

class Bumblebee:
    huggingFace = None

    @classmethod
    def createHuggingFace(cls,modelName,device,normalizeEmbeddings):
        cls.huggingFace = HuggingFaceBgeEmbeddings(
                model_name=modelName,
                model_kwargs={"device": device},
                encode_kwargs={"normalize_embeddings": normalizeEmbeddings},
            )


    @staticmethod
    async def createAndStoreVectors(
        topic_uuid:str,
        logger : object,
        chunkSize : int,
        chunkOverlap : int,
        modelName : str,
        device : str,
        normalizeEmbeddings : bool,
        folder_name : str
        )->bool:
        try:
            logger.info(f"reading file from folder {topic_uuid}")
            loader = PyPDFDirectoryLoader(folder_name)
            docs_before_split = loader.load()
            logger.info(f"creating chuncks {topic_uuid}")
            # text_splitter = RecursiveCharacterTextSplitter(chunkSize, chunk_overlap=chunkOverlap)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size = 700,
                chunk_overlap  = 50,
            )
            docs_after_split = text_splitter.split_documents(docs_before_split)
            logger.info(f"starting embedding {topic_uuid}")
            logger.info(f"creating vectore store {topic_uuid}")
            vectorstore = FAISS.from_documents(docs_after_split, Bumblebee.huggingFace)
            logger.info(f"converting data into binary {topic_uuid}")
            vectorData = vectorstore.serialize_to_bytes()
            logger.info(f"storeing binary into db {topic_uuid}")
            await UserFileEmbedding(
                topic_uuid = topic_uuid,
                folder_name = folder_name,
                embeddingBinary = vectorData
            ).save()
            logger.info(f"binary store into db {topic_uuid}")
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"failed to create and store document binary into db due to {e} for {topic_uuid}")
    
    @staticmethod
    async def getAnswer(query: str,topic_uuid:str,logger:object):
        try:
            logger.info("trying to getting byte strings")
            embedding = await UserFileEmbedding.get(topic_uuid = topic_uuid)
            if not embedding.isAllow:
                logger.error("sorry user deactivate this topic")
                return {
                    "status":False,
                    "reason":"failed due to no object found"
                }
            logger.info("restoring vector store")         
            vectorstore = FAISS.deserialize_from_bytes(embedding.embeddingBinary,Bumblebee.huggingFace,allow_dangerous_deserialization=True)
            logger.info("guru j reading your question")  
            relevant_documents = vectorstore.similarity_search(query)
            result = {i:a.page_content for i,a in enumerate(relevant_documents)}
            logger.info("guru j answer sended")  
            return {
                "status":True,
                "result":result
            }
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"failed due to {e}")
            return {
                "status":False,
                "reason":f"failed due to {e}"
            }
       