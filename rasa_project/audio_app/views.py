import os
import tempfile
import shutil
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .MyDejavu import Dejavu
from hashlib import sha1
from .models import *
from rest_framework.permissions import IsAuthenticated

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
            raise e
            self.clean_up(temp_dir)
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
        


class AudioBaseView(APIView):
    """Base class for handling audio uploads and Dejavu fingerprinting."""
    parser_classes = (MultiPartParser,)

    def get_dejavu_instance(self):
        """Returns a configured Dejavu instance."""
        config = {
            "database": {
                "host": "database-1.cba0e6ewsm1v.eu-north-1.rds.amazonaws.com",  # AWS RDS endpoint
                "user": "admin",  # Master username from RDS
                "password": "Maje1234$$",  # Master password from RDS
                "database": "dejavu",  # The name of your database (you may need to create this in RDS)
            },
            "database_type": "mysql",  # MySQL as the database type
            "fingerprint_limit": 10,
        }
        return Dejavu.Dejavu(config)


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


class FingerPrintAudio(AudioBaseView):
    """
    API endpoint to upload an audio file and create its fingerprint.
    """
    
    @swagger_auto_schema(
        operation_description="Upload an audio file and fingerprint it.",
        manual_parameters=[
            openapi.Parameter(
                'file', openapi.IN_FORM, description="Audio file to upload", type=openapi.TYPE_FILE, required=True
            )
        ],
        responses={200: "Audio successfully fingerprinted"},
        consumes=['multipart/form-data'],
    )
    def post(self, request, **kwargs):
        if 'file' not in request.FILES:
            return Response({'success': False, 'message': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_path, temp_dir = self.handle_uploaded_file(request.FILES['file'])
            djv = self.get_dejavu_instance()
            djv.fingerprint_file(file_path)

            return Response({'success': True, 'message': 'Audio successfully fingerprinted'}, status=status.HTTP_200_OK)

        except Exception as e:
            raise e
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        finally:
            self.clean_up(temp_dir)


class CheckAudioFingerprint(AudioBaseView):
    """
    API endpoint to check if an audio file's fingerprint exists in the database.
    """

    @swagger_auto_schema(
        operation_description="Upload an audio file and check if its fingerprint exists.",
        manual_parameters=[
            openapi.Parameter(
                'file', openapi.IN_FORM, description="Audio file to upload", type=openapi.TYPE_FILE, required=True
            )
        ],
        responses={200: "Check complete"},
        consumes=['multipart/form-data'],
    )
    def post(self, request, **kwargs):
        if 'file' not in request.FILES:
            return Response({'success': False, 'message': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_path, temp_dir = self.handle_uploaded_file(request.FILES['file'])
            djv = self.get_dejavu_instance()

            fingerprint_result = djv.check_if_audio_file_exists(file_path)
            if fingerprint_result['status']:
                return Response({
                    'success': True,
                    'message': 'Audio already exists in the database',
                    'details': fingerprint_result['details']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Audio does not exist in the database',
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        finally:
            self.clean_up(temp_dir)
