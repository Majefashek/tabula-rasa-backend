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

class AudioBaseView(APIView):
    """Base class for handling audio uploads and Dejavu fingerprinting."""
    parser_classes = (MultiPartParser,)

    def get_dejavu_instance(self):
        """Returns a configured Dejavu instance."""
        config = {
            "database": {
                "host": "127.0.0.1",
                "user": "root",
                "password": "1234maje",
                "database": "dejavu",
            },
            "database_type": "mysql",
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
