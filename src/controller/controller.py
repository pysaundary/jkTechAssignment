from fastapi import HTTPException, APIRouter ,FastAPI, File, UploadFile,BackgroundTasks
from tortoise.contrib.fastapi import HTTPNotFoundError
import uuid
import os
import asyncio

from src.models.models import UserFilesModel
from src.schemas.schemas import DocumentIngestionRequest, QuestionRequest, AnswerResponse
from src.utilities.transformer import generate_embedding
import src.constant as constants
from src.utilities.transformers.autobot import Bumblebee

llmRouter = APIRouter()

@llmRouter.post("/ingest", status_code=201)
async def ingest(data: DocumentIngestionRequest):
    return await ingest_document(data)

@llmRouter.post("/ask", response_model=AnswerResponse)
async def ask(data: QuestionRequest):
    return await ask_question(data)

@llmRouter.get("/documents")
async def get_documents():
    return await list_documents()

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
    transformerKwagrs = {
        "folder_path":base_dir,
        "topic_uuid" : uuid_data,
        "modelName":constants.singletonObjectDict.get("transformer",{}).get("model_name"),
        "device":constants.singletonObjectDict.get("transformer",{}).get("device"),
        "normalizeEmbeddings":constants.singletonObjectDict.get("transformer",{}).get("normalizeEmbeddings"),
        "chunkSize":constants.singletonObjectDict.get("transformer",{}).get("chunkSize"),
        "chunkOverlap":constants.singletonObjectDict.get("transformer",{}).get("chunkOverlap")
    }
    transformerObject = Bumblebee(**transformerKwagrs)
    asyncio.create_task(transformerObject.createVector())
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




async def ingest_document(data: DocumentIngestionRequest):
    """
    Handles document ingestion by generating embeddings and saving the document to the database.
    """
    embedding = generate_embedding(data.content)
    doc = await Document.create(
        title=data.title, content=data.content, embeddings=embedding
    )
    return {"message": "Document ingested successfully", "document_id": doc.id}

async def ask_question(request: QuestionRequest):
    document = await Document.filter(id=request.document_ids[0]).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    question_keywords = request.question.lower().split()
    relevant_content = []

    for line in document.content.split("\n"):
        if any(keyword in line.lower() for keyword in question_keywords):
            relevant_content.append(line.strip())

    if relevant_content:
        return AnswerResponse(answer=" ".join(relevant_content))
    else:
        return AnswerResponse(answer="No relevant content found.")

async def list_documents():
    """
    Lists all documents in the database.
    """
    documents = await Document.all()
    return [{"id": doc.id, "title": doc.title} for doc in documents]
