import boto3
from django.conf import settings
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import logging

logger = logging.getLogger(__name__)

def generate_s3_signed_url(file_name, content_type, expiration=3600):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    try:
        signed_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': file_name,
                'ContentType': content_type
            },
            ExpiresIn=expiration
        )
        return signed_url
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error(f"Error generating signed URL: {e}")
        return None
