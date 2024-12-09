from tortoise.models import Model
from tortoise import fields


class Document(Model):
    id = fields.IntField(pk=True)
    title = fields.TextField()
    content = fields.TextField()
    embeddings = fields.JSONField()  

# class Embedding(Model):
#     id = fields.IntField(pk=True)
#     document = fields.ForeignKeyField("models.Document", related_name="embeddings")
#     vector = fields.JSONField()  # Store embedding as a JSON array
#     created_at = fields.DatetimeField(auto_now_add=True)
