from fastapi import HTTPException, APIRouter , File, UploadFile
import uuid
import os
import traceback
import traceback

from src.models.models import UserFilesModel,UserFileEmbedding
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
    try:
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
        transformerData = constants.singletonObjectDict.get("transformer",{})
        await Bumblebee.createAndStoreVectors(
            topic_uuid = uuid_data,
            logger = constants.internalLoggers.get("transformer_logs",None),
            chunkOverlap = transformerData.get("chunk_overlap",50),
            chunkSize = transformerData.get("chunk_size",700),
            device = transformerData.get("device","cpu"),
            modelName = transformerData.get("model_name","BAAI/bge-small-en-v1.5"),
            normalizeEmbeddings = transformerData.get("normalize_embeddings",True),
            folder_name=base_dir
        )
        return {"uploaded_files": uploaded_files}
    except Exception as e:
        api_logger.error(traceback.format_exc())
        api_logger.error(f"failed to upload document due to {e}")

@llmRouter.get("/get_user_files/")
async def getUserFiles(user_id : str,limit :int = 10 ,order_by : bool = True ,offset : int =0 ,topicName = None):
    api_logger = constants.internalLoggers.get("apis_logs",None)
    try:
        userDocs = await UserFilesModel.getUserDocumentList(user_id,limit,order_by,offset,topicName)
        return userDocs
    except Exception as e:
        api_logger.error(f"Error due to {e}")
        api_logger.error(traceback.format_exc())
        return {"error": f"Error due to {e}"}

@llmRouter.post("/ask-question/")
async def askQuestions(requestData: QuestionSchema):
    api_logger = constants.internalLoggers.get("apis_logs", None)
    transformer_logger = constants.internalLoggers.get("transformer_logs", None)
    try:
        result = await Bumblebee.getAnswer(
            query=requestData.question,
            topic_uuid=requestData.topicUUID,
            logger=transformer_logger
        )
        return result
    except Exception as e:
        api_logger.error(f"failed due to {e}")
        return {
            "status":False,
            "reason":f"failed api due to {e}"
        }
    
@llmRouter.get('/enable-and-disable-topic/')
async def enableAndDisableTopic(topic_uuid : str,isActive : bool = True):
    api_logger = constants.internalLoggers.get("apis_logs", None)
    try:
        embedding = await UserFileEmbedding.get(topic_uuid = topic_uuid)  
        embedding.isAllow = isActive
        await embedding.save()
        api_logger.info(f"updated {topic_uuid} done")
        return {
            "status":True,
            "msg":"update process done"
        }
    except Exception as e:
        api_logger.error(f"failed to update {topic_uuid}")
        return {
            "status":False,
            "reason":f"failed due to {e}"
        }