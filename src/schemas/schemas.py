from pydantic import BaseModel
from typing import List


class DocumentIngestionRequest(BaseModel):
    title: str
    content: str


class QuestionRequest(BaseModel):
    question: str
    document_ids: List[int] = None


class AnswerResponse(BaseModel):
    answer: str
