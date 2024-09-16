import os
import tempfile
import shutil
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from hashlib import sha1
from .models import *
from rest_framework.permissions import IsAuthenticated

from django.http import JsonResponse
from .utils import generate_s3_signed_url

from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from django.http import JsonResponse
from datetime import datetime

class GetSignedUrl(APIView):
    permission_classes = [IsAuthenticated]
    #parser_classes = [MultiPartParser]  # Handles multipart/form-data requests
    
    @swagger_auto_schema(
        operation_description="Generate a signed URL for uploading a file to an S3 bucket. "
                              "The client provides the file name and content type, and receives "
                              "a pre-signed URL for secure file upload. The file itself is not uploaded "
                              "via this endpoint; instead, the client uses the returned signed URL "
                              "to upload the file directly to the S3 bucket.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'file_name': openapi.Schema(type=openapi.TYPE_STRING, description='The name of the file to be uploaded'),
                'content_type': openapi.Schema(type=openapi.TYPE_STRING, description='The content type (MIME type) of the file'),
            },
            required=['file_name', 'content_type'],
        ),
        responses={200: "A pre-signed URL for uploading the file to S3."},
        consumes=['multipart/form-data'],
    )
    def post(self, request):
        file_name = request.data.get('file_name')
        content_type = request.data.get('content_type')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_path=f'{request.user.id}/audio/{file_name}_{timestamp}/{content_type}'
        
        if not file_name or not content_type:
            return JsonResponse({'success':False,'error': 'file_name and content_type are required'}, status=400)
        
        signed_url = generate_s3_signed_url(file_path, content_type)
        if signed_url:
            return JsonResponse({'success':True,'signed_url': signed_url},status=200)
        return JsonResponse({'success':False,'error': 'Could not generate signed URL'}, status=500)
    

class CheckIfAudioHashExist(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Check if an audio file hash already exists in the database.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'hash': openapi.Schema(type=openapi.TYPE_STRING, description='The hash of the audio file'),
            },
            required=['hash'],
        ),
        responses={
            200: openapi.Response(description='Hash existence status', examples={
                'application/json': {
                    'exists': True
                }
            }),
            400: 'Invalid request body',
        },
    )
    def post(self, request):
        hash_value = request.data.get('hash')
        
        if not hash_value:
            return Response({'success': False, 'error': 'Hash is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = MyAudioFile.objects.filter(file_hash=hash_value).exists()
        return Response({'success': True, 'exists': exists}, status=status.HTTP_200_OK)
    

class StoreAudioDetailsHashAndS3Key(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Store audio details including hash and S3 key in the database.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'hash': openapi.Schema(type=openapi.TYPE_STRING, description='The hash of the audio file'),
                's3_key': openapi.Schema(type=openapi.TYPE_STRING, description='The S3 key where the file is stored'),
                'file_name': openapi.Schema(type=openapi.TYPE_STRING, description='The name of the file'),
            },
            required=['hash', 's3_key', 'file_name'],
        ),
        responses={
            200: 'Audio details successfully stored',
            400: 'Invalid request body',
        },
    )
    def post(self, request):
        try:
            hash_value = request.data.get('hash')
            s3_key = request.data.get('s3_key')
            file_name = request.data.get('file_name')
            
            if not hash_value or not s3_key or not file_name:
                return Response({'success': False, 'error': 'Hash, s3_key, and file_name are required'}, status=status.HTTP_400_BAD_REQUEST)
            
            
            MyAudioFile.objects.create(
                contributor=request.user,
                file_hash=hash_value,
                s3_key=s3_key,
                file_name=file_name
            )
            
            return Response({'success': True, 'message': 'Audio details successfully stored'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER)









''''
class MyAudioBaseView(APIView):
    """Base class for handling audio uploads and Dejavu fingerprinting."""
    parser_classes = (MultiPartParser,)

    def handle_uploaded_file(self, file):
        """Handles file upload and saves it to a temporary directory."""
        temp_dir = tempfile.mkdtemp()
        try:
            file_path = os.path.join(temp_dir, file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            return file_path, temp_dir
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise e

    def clean_up(self, temp_dir):
        """Removes the temporary directory created during file handling."""
        shutil.rmtree(temp_dir, ignore_errors=True)

    def unique_hash(self, filepath, blocksize=2**20):
        """Generates a unique hash for the audio file."""
        s = sha1()
        with open(filepath, "rb") as f:
            while True:
                buf = f.read(blocksize)
                if not buf:
                    break
                s.update(buf)
        return s.hexdigest().upper()


class CheckAndSaveAudioHash(MyAudioBaseView):
    permission_classes = [IsAuthenticated]
    
    """
    API endpoint to upload an audio file, check if it already exists, 
    and save the file name and hash if it's unique.
    """
    
    @swagger_auto_schema(
        operation_description="Upload an audio file, hash it, and check if the hash already exists.",
        manual_parameters=[
            openapi.Parameter(
                'file', openapi.IN_FORM, description="Audio file to upload", type=openapi.TYPE_FILE, required=True
            ),
             openapi.Parameter(
            'url', openapi.IN_FORM, description="URL of the audio file in ss3", type=openapi.TYPE_STRING, required=False
        )

        ],
        responses={200: "Audio successfully fingerprinted"},
        consumes=['multipart/form-data'],
    )
    def post(self, request, **kwargs):
        if 'file' not in request.FILES:
            return Response({'success': False, 'message': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        

        # Handle file upload
        file = request.FILES['file']
        myaudio_url=request.data.get('url')
        file_path, temp_dir = self.handle_uploaded_file(file)

        try:
            # Generate a unique hash for the file
            file_hash = self.unique_hash(file_path)

            # Check if hash already exists
            if MyAudioFile.objects.filter(file_hash=file_hash).exists():
                self.clean_up(temp_dir)
                return Response({'success': False, 'message': 'File with this hash already exists'}, status=status.HTTP_409_CONFLICT)

            # Save file name and hash to the database
            audio_file = MyAudioFile.objects.create(file_name=file.name, file_hash=file_hash, myaudio_url=myaudio_url,contributor=request.user)
            
            # Cleanup the temp directory
            self.clean_up(temp_dir)

            return Response({'success': True, 'message': 'Audio successfully and Recorded', 'file_hash': file_hash}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            #raise e
            self.clean_up(temp_dir)
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        
'''