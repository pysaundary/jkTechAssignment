from fastapi import HTTPException, APIRouter
from src.models.models import Document
from src.schemas.schemas import DocumentIngestionRequest, QuestionRequest, AnswerResponse
from src.utilities.transformer import generate_embedding
from typing import List
import torch

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

async def ingest_document(data: DocumentIngestionRequest):
    """
    Handles document ingestion by generating embeddings and saving the document to the database.
    """
    embedding = generate_embedding(data.content)
    doc = await Document.create(
        title=data.title, content=data.content, embeddings=embedding
    )
    return {"message": "Document ingested successfully", "document_id": doc.id}


# async def ask_question(data: QuestionRequest):
#     """
#     Handles Q&A requests by retrieving the most relevant document and generating an answer.
#     """
#     # Retrieve embeddings from selected documents
#     if data.document_ids:
#         docs = await Document.filter(id__in=data.document_ids).all()
#     else:
#         docs = await Document.all()

#     if not docs:
#         raise HTTPException(status_code=404, detail="No documents found")

#     # Generate question embedding
#     question_embedding = generate_embedding(data.question)

#     # Find the most relevant document (cosine similarity)
#     similarities = [
#         (doc, torch.cosine_similarity(
#             torch.tensor(doc.embeddings),
#             torch.tensor(question_embedding)
#         ).item())
#         for doc in docs
#     ]
#     most_relevant_doc = max(similarities, key=lambda x: x[1])[0]

#     # Generate answer (mock example; replace with RAG logic)
#     answer = f"Answer generated from document '{most_relevant_doc.title}'"
#     return {"answer": answer}

async def ask_question(request: QuestionRequest):
    # Fetch document by ID
    document = await Document.filter(id=request.document_ids[0]).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Perform a simple keyword match to find the relevant content (you can improve this)
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
