from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class ImageDB(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    img_id = models.CharField(max_length=1000)
    img_desc = models.CharField(max_length=1000)
    img_path = models.CharField(max_length=1000)

    def __str__(self):
        return self.img_id


class FaceEmbedding(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    embedding_path = models.CharField(max_length=1000)
    embedding_id_path = models.CharField(max_length=1000)

    def __str__(self):
        return self.embedding_path