from tortoise.models import Model
from tortoise import fields
from pathlib import Path
from tortoise.queryset import QuerySet
from typing import List, Dict, Any
from tortoise.expressions import Q ,F

import src.constant as constants

class UserFilesModel(Model):
    id = fields.IntField(pk=True)
    user = fields.CharField(max_length=50)
    topic = fields.TextField()
    topic_uuid = fields.UUIDField(null = True)
    file_path = fields.CharField(max_length=255)
    file_url = fields.CharField(max_length=555)
    folder_name = fields.CharField(max_length=555)

    class Meta:
        table = "files"


    @staticmethod
    async def createFilePath(**kwargs) -> str:
        try:
            # Define base directory and folder structure
            folder_name = f"{kwargs.get('user_id')}_{kwargs.get('uuid')}_{kwargs.get('topic')}"
            base_dir = Path(constants.BASE_DIR) / "media" / folder_name
            # Construct file path
            url = f"""{constants.singletonObjectDict.get("app_data",{}).get("host","localhost")}:{constants.singletonObjectDict.get("app_data",{}).get("port",8003)}/{constants.singletonObjectDict.get("app_data",{}).get("media","media")}/{folder_name}"""
            file_path = base_dir / kwargs.get("filename")
            # Ensure the path is in OS-specific format
            return str(file_path), str(url) ,str(base_dir)
        except Exception as e:
            raise Exception(f"failed due to {e}")

    @staticmethod
    async def getUserDocumentList(user_id: str, limit: int = 10, order_by: bool = True, offset: int = 1,topicName = None) -> Dict[str, Any]:
        order = "topic_uuid" if order_by else "-topic_uuid"
        offset = max(0, offset - 1)
        # Filter for unique topics first (more efficient for larger datasets)
        if topicName:
            unique_topics = await UserFilesModel.filter(user=user_id,topic = topicName).order_by(order).limit(limit).offset(offset).distinct().values("topic", "topic_uuid")
        else:
            unique_topics = await UserFilesModel.filter(user=user_id).order_by(order).limit(limit).offset(offset).distinct().values("topic", "topic_uuid")
        count = len(unique_topics)
        
        # return result
        for topic in unique_topics:
            topic["embeddings"] = await UserFileEmbedding.filter(topic_uuid=topic["topic_uuid"], isAllow=True).count()
        result = {
            "count":count,
            "result" : unique_topics
        }
        return result

class UserFileEmbedding(Model):
    topic_uuid = fields.UUIDField(pk=True)
    folder_name = fields.CharField(max_length=555)
    isAllow = fields.BooleanField(default = True)
    embeddingBinary = fields.BinaryField()
    class Meta:
        table = "files_embeddings"

