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
# Create your views here.

UTILS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),'utils')
FACE_EMBEDDING_DIR = os.path.join(UTILS_DIR,'data')
IMG_DIR = os.path.join(UTILS_DIR,'images')


class SignUp(APIView):

    def randomString(self, len=5):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(len))

    def post(self, request):
        username = request.data['username']
        password = request.data['password']
        email = request.data['email']

        try:
            user = User.objects.create_user(username=username, password=password, email=email)
            curr_time = datetime.datetime.now()
            curr_time_str = curr_time.strftime("%Y%M%d_%H%M%S")
            rand_str = self.randomString()
            embedding_face_pathname = rand_str + '_' + curr_time_str + '.pkl'
            embedding_face_id_pathname = rand_str + '_id_' + curr_time_str + '.pkl'
            embedding_face_path = os.path.join(FACE_EMBEDDING_DIR, embedding_face_pathname)
            embedding_face_id_path = os.path.join(FACE_EMBEDDING_DIR, embedding_face_id_pathname)

            db_model = FaceEmbedding()
            db_model.user_id = user
            db_model.embedding_id_path = embedding_face_id_path
            db_model.embedding_path = embedding_face_path
            db_model.save()

            content = {'message': 'SignUp successful'}
        except:
            if User.objects.filter(username=username).exists():
                content = {'message': 'Username exists!'}
            elif User.objects.filter(email=email).exists():
                content = {'message': 'Email exists!'}
            else:
                content = {'message': 'Unable to signup!'}

        return Response(content)


class UploadImage(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        img_id = request.data['img_id']
        img_desc = request.data['img_desc']
        img_file = request.FILES['image']

        mime_type = magic.from_buffer(img_file.open().read(1024).lower())

        if not ('png' in mime_type.lower() or 'jpeg' in mime_type.lower() or 'bmp' in mime_type.lower()):
            content = {'message': 'Not an image file'}
        else:
            fs = FileSystemStorage(IMG_DIR)
            img_filename = fs.save(img_file.name, img_file)
            img_filepath = os.path.join(IMG_DIR, img_filename)

            db_model = ImageDB()
            db_model.user_id = request.user
            db_model.img_id = img_id
            db_model.img_desc = img_desc
            db_model.img_path = img_filepath
            db_model.save()

            face_embeddings = face_recog.get_embeddings(img_filepath)

            content = {'message': 'Added to DB'}
        return Response(content)


class DeleteID(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        img_id = request.data['img_id']
        content = {'message': 'Added to DB'}
        return Response(content)


class AnalyzeImage(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        img_file = request.FILES['image']

        content = {'message': 'Hello, World!'}
        return Response(content)