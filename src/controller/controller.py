from fastapi import HTTPException, APIRouter ,FastAPI, File, UploadFile,BackgroundTasks
from tortoise.contrib.fastapi import HTTPNotFoundError
import uuid
import os
import asyncio
from tortoise.exceptions import DoesNotExist

from src.models.models import UserFilesModel,UserFileEmbedding
from src.schemas.schemas import DocumentIngestionRequest, QuestionRequest, AnswerResponse
from src.utilities.transformer import generate_embedding
import src.constant as constants
from src.utilities.transformers.autobot import Bumblebee
from src.schemas.schemas import QuestionSchema

llmRouter = APIRouter()

@llmRouter.post("/upload_files/")
async def create_upload_files(files: list[UploadFile] = File(...), user_id: str = None ,topic : str = None ):
    """
    Uploads one or multiple PDF files and saves them to a specific folder.

    Args:
        files: A list of uploaded files.
        user_id: The ID of the user uploading the files.

    Returns:
        A JSON response indicating success or failure.
    """
    api_logger = constants.internalLoggers.get("apis_logs",None)
    if not user_id:
        api_logger.error("User ID is required")
        raise HTTPException(status_code=400, detail="User ID is required")
    if not topic :
        api_logger.error("Topic name is required")
        raise HTTPException(status_code=400, detail="Topic name is required")
    uploaded_files = []
    uuid_data = uuid.uuid4()
    for file in files:
        if file.filename.endswith(".pdf"):
            kwarg_values = {
                "user_id" : user_id,
                "uuid" : uuid_data,
                "topic" : topic,
                "filename" : file.filename
            } 
            file_path, file_url, base_dir  = await UserFilesModel.createFilePath(**kwarg_values)
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "wb") as buffer:
                    buffer.write(file.file.read())
                file_model = UserFilesModel(
                    user = user_id,
                    topic = topic,
                    file_path = file_path,
                    file_url = file_url,
                    folder_name = base_dir,
                    topic_uuid = uuid_data
                 )
                await file_model.save()
                uploaded_files.append({"filename": file.filename})
            except Exception as e:
                api_logger.error(f"Error uploading file: {e}")
                return {"error": f"Error uploading file due to : {e}"}
        else:
            api_logger.error("Only PDF files are allowed")
            return {"error": "Only PDF files are allowed"}
    uFE = UserFileEmbedding(
                    topic_uuid = uuid_data,
                    folder_name = base_dir
                )
    await uFE.save()
    return {"uploaded_files": uploaded_files}

@llmRouter.get("/get_user_files/")
async def getUserFiles(user_id : str):
    api_logger = constants.internalLoggers.get("apis_logs",None)
    try:
        userDocs = await UserFilesModel.getUserDocumentList(user_id)
        return userDocs
    except Exception as e:
        api_logger.error(f"Error due to {e}")
        return {"error": f"Error due to {e}"}

@llmRouter.post("/ask-question/")
async def askQuestions(requestData: QuestionSchema):
    api_logger = constants.internalLoggers.get("apis_logs", None)
    try:
        # Fetch embedding metadata
        data = await UserFileEmbedding.get(topic_uuid=requestData.topicUUID)
        a = 123
        # Prepare transformer arguments
        transformerKwagrs = {
            "folder_path": data.folder_name,
            "topic_uuid": data.topic_uuid,
            "modelName": constants.singletonObjectDict.get("transformer", {}).get("model_name"),
            "device": constants.singletonObjectDict.get("transformer", {}).get("device"),
            "normalizeEmbeddings": constants.singletonObjectDict.get("transformer", {}).get("normalizeEmbeddings"),
            "chunkSize": constants.singletonObjectDict.get("transformer", {}).get("chunkSize"),
            "chunkOverlap": constants.singletonObjectDict.get("transformer", {}).get("chunkOverlap"),
        }
        
        # Initialize Bumblebee and fetch answer
        transformer = Bumblebee(**transformerKwagrs)
        answer = await transformer.createAndCheckAnswer(requestData.question)
        
        # Log and return the answer
        api_logger.info(f"Answer fetched successfully for topic UUID {requestData.topicUUID}")
        return {"answer": answer}
    
    except DoesNotExist:
        api_logger.error(f"No embeddings found for topic UUID {requestData.topicUUID}")
        return {"error": f"No embeddings found for topic UUID {requestData.topicUUID}"}
    
    except Exception as e:
        api_logger.error(f"Failed to process request due to: {e}")
        return {"error": f"An internal error occurred: {e}"}
