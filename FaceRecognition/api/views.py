from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.files.storage import FileSystemStorage
from rest_framework.permissions import IsAuthenticated  # <-- Here

from .models import *
from .utils import face_recog
import os
import datetime
import string, random
import magic
import pickle as pkl
import numpy as np

# Create your views here.

UTILS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "utils")
FACE_EMBEDDING_DIR = os.path.join(UTILS_DIR, "data")
IMG_DIR = os.path.join(UTILS_DIR, "images")


class SignUp(APIView):
    def randomString(self, len=5):
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for i in range(len))

    def post(self, request):
        username = request.data["username"]
        password = request.data["password"]
        email = request.data["email"]

        try:
            user = User.objects.create_user(
                username=username, password=password, email=email
            )
            curr_time = datetime.datetime.now()
            curr_time_str = curr_time.strftime("%Y%M%d_%H%M%S")
            rand_str = self.randomString()
            embedding_face_pathname = rand_str + "_" + curr_time_str + ".pkl"
            embedding_face_path = os.path.join(
                FACE_EMBEDDING_DIR, embedding_face_pathname
            )

            db_model = FaceEmbedding()
            db_model.user_id = user
            db_model.embedding_path = embedding_face_path
            db_model.save()

            content = {"message": "SignUp successful"}
        except:
            if User.objects.filter(username=username).exists():
                content = {"message": "Username exists!"}
            elif User.objects.filter(email=email).exists():
                content = {"message": "Email exists!"}
            else:
                content = {"message": "Unable to signup!"}

        return Response(content)


class UploadImage(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        img_id = request.data["image_id"]
        img_desc = request.data["image_desc"]
        img_file = request.FILES["image"]

        if ImageDB.objects.filter(img_id=img_id).exists():
            content = {"message": "ID already exists!"}
            return Response(content)

        mime_type = magic.from_buffer(img_file.open().read(1024).lower())

        if not (
            "png" in mime_type.lower()
            or "jpeg" in mime_type.lower()
            or "bmp" in mime_type.lower()
        ):
            content = {"message": "Not an image file"}
        else:
            fs = FileSystemStorage(IMG_DIR)
            img_filename = fs.save(img_file.name, img_file)
            img_filepath = os.path.join(IMG_DIR, img_filename)

            response = face_recog.get_embeddings(img_filepath)
            try:
                values = response["result"]["values"]

                if len(values) >= 2:
                    content = {"message": "Too many faces detected!"}
                elif len(values) == 0:
                    content = {"message": "No faces detected!"}
                else:
                    objects = FaceEmbedding.objects.filter(user_id=request.user)
                    if len(objects) == 0:
                        content = {"message": "Something's really wrong"}
                        return Response(content)

                    face_embeddings = values[0][0]

                    db_row = objects[0]
                    embedding_path = db_row.embedding_path

                    if os.path.isfile(embedding_path):
                        temp_dict = pkl.load(open(embedding_path, "rb"))
                        temp_dict[img_id] = face_embeddings
                        pkl.dump(temp_dict, open(embedding_path, "wb"))
                    else:
                        temp_dict = dict()
                        temp_dict[img_id] = face_embeddings
                        pkl.dump(temp_dict, open(embedding_path, "wb"))

                    db_model = ImageDB()
                    db_model.user_id = request.user
                    db_model.img_id = img_id
                    db_model.img_desc = img_desc
                    db_model.img_path = img_filepath
                    db_model.save()
                    content = {"message": "Added to DB"}
            except Exception as e:
                print(e)
                content = {"message": response["message"]}

        return Response(content)


class DeleteID(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        img_id = request.data["image_id"]

        objects = ImageDB.objects.filter(img_id=img_id)
        if not objects.exists():
            content = {"message": "ID doesn't exist!"}
            return Response(content)

        if len(objects) != 1:
            content = {
                "message": "Multiple IDs detected. Not possible! Something's wrong in UpdateImage view."
            }
            return Response(content)

        objects = FaceEmbedding.objects.filter(user_id=request.user)
        if len(objects) != 1:
            content = {"message": "Something's really wrong!"}
            return Response(content)

        db_row = objects[0]
        embedding_path = db_row.embedding_path
        if os.path.isfile(embedding_path):
            temp_dict = pkl.load(open(embedding_path, "rb"))
            val = temp_dict.pop(img_id, None)
            pkl.dump(temp_dict, open(embedding_path, "wb"))
            if val:
                objects[0].delete()  # Deleting row from ImageDB
                content = {"message": "Relevant face embedding has been deleted"}
            else:
                content = {
                    "message": "Something's wrong! Exists in DB but not in pkl file"
                }

        else:
            content = {"message": "Sorry embeddings don't exist"}

        return Response(content)


class AnalyzeImage(APIView):
    permission_classes = (IsAuthenticated,)

    def cosine_similarity(self, x, y):
        x = np.array(x)
        y = np.array(y)
        return np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y))

    def find_similar(self, test_embed, face_embeddings):
        length = len(face_embeddings)
        similar_faces = []

        for face_embed_id, face_embedding in face_embeddings.items():
            val = self.cosine_similarity(face_embedding, test_embed)
            similar_faces.append((face_embed_id, val))

        similar_faces = sorted(similar_faces, key=lambda x: x[1], reverse=True)
        return similar_faces

    def post(self, request):
        img_file = request.FILES["image"]

        mime_type = magic.from_buffer(img_file.open().read(1024).lower())

        if not (
            "png" in mime_type.lower()
            or "jpeg" in mime_type.lower()
            or "bmp" in mime_type.lower()
        ):
            content = {"message": "Not an image file", "result": None}
            return Response(content)

        fs = FileSystemStorage(IMG_DIR)
        img_filename = fs.save(img_file.name, img_file)
        img_filepath = os.path.join(IMG_DIR, img_filename)

        objects = FaceEmbedding.objects.filter(user_id=request.user)
        if len(objects) != 1:
            content = {"message": "Something's really wrong!", "result": None}
            return Response(content)

        db_row = objects[0]
        embedding_path = db_row.embedding_path
        if not os.path.isfile(embedding_path):
            content = {"message": "No embeddings found in DB!", "result": None}
            return Response(content)

        response = face_recog.get_embeddings(img_filepath)

        try:
            face_embeddings = pkl.load(open(embedding_path, "rb"))
            values = response["result"]["values"]
            match_face = []

            for val in values:
                face_embed, bbox = val
                similar_imgs = self.find_similar(face_embed, face_embeddings)
                match_face.append((similar_imgs, bbox))

            result = {"values": match_face}
            content = {"message": "Success", "result": result}

        except Exception as e:
            print(e)
            content = {"message": response["message"], "result": None}

        # Cleanup uploaded image
        os.remove(img_filepath)

        return Response(content)
