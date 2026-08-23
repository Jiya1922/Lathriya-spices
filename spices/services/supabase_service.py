import os
import logging
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)

def get_s3_client():
    """Returns an initialized S3 client for Supabase Storage using credentials from settings/environment."""
    s3_key = getattr(settings, 'SUPABASE_STORAGE_S3_KEY_ID', '') or os.getenv('SUPABASE_STORAGE_S3_KEY_ID', '').strip()
    s3_secret = getattr(settings, 'SUPABASE_STORAGE_S3_SECRET_KEY', '') or os.getenv('SUPABASE_STORAGE_S3_SECRET_KEY', '').strip()
    s3_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', '') or os.getenv('SUPABASE_STORAGE_S3_ENDPOINT', '').strip()
    s3_region = getattr(settings, 'AWS_S3_REGION_NAME', 'ap-southeast-1') or os.getenv('SUPABASE_STORAGE_REGION', 'ap-southeast-1').strip()

    if not s3_key or not s3_secret or not s3_endpoint:
        raise ValueError("Supabase Storage S3 credentials (KEY_ID, SECRET_KEY, ENDPOINT) are not configured in settings/environment.")

    return boto3.client(
        's3',
        aws_access_key_id=s3_key,
        aws_secret_access_key=s3_secret,
        endpoint_url=s3_endpoint,
        region_name=s3_region
    )

def ensure_bucket_exists(s3_client, bucket_name):
    """Checks if the Supabase bucket exists; creates it if missing."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code in ('404', 'NoSuchBucket'):
            logger.info(f"Bucket '{bucket_name}' does not exist on Supabase. Creating bucket...")
            try:
                s3_client.create_bucket(Bucket=bucket_name)
                logger.info(f"Successfully created bucket '{bucket_name}' on Supabase Storage.")
            except Exception as create_err:
                logger.warning(f"Could not explicitly create bucket '{bucket_name}': {create_err}")
        else:
            logger.warning(f"head_bucket status for '{bucket_name}': {e}")

def upload_receipt_to_supabase(file_data, payment_id, created_at=None):
    """
    Uploads PDF binary file_data to Supabase Storage bucket 'payment-receipts'.
    
    Path structure:
    payment-receipts/YYYY/MM/pay_xxxxxxxxx.pdf
    
    Returns:
    (receipt_path, receipt_url)
    """
    bucket_name = os.getenv('SUPABASE_RECEIPTS_BUCKET', 'payment-receipts').strip()
    dt = created_at or datetime.now()
    year_str = dt.strftime('%Y')
    month_str = dt.strftime('%m')

    # Sanitize payment_id for filename
    clean_pid = str(payment_id).strip()
    filename = f"{clean_pid}.pdf" if not clean_pid.endswith('.pdf') else clean_pid
    
    # Relative object path inside bucket
    object_path = f"{year_str}/{month_str}/{filename}"
    full_storage_path = f"{bucket_name}/{object_path}"

    try:
        s3 = get_s3_client()
        ensure_bucket_exists(s3, bucket_name)

        logger.info(f"Uploading receipt PDF to Supabase bucket '{bucket_name}' at path '{object_path}'...")
        s3.put_object(
            Bucket=bucket_name,
            Key=object_path,
            Body=file_data,
            ContentType='application/pdf',
            CacheControl='public, max-age=31536000'
        )

        # Generate presigned or public URL
        s3_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', '') or os.getenv('SUPABASE_STORAGE_S3_ENDPOINT', '').strip()
        
        # Build direct Supabase Storage public/presigned URL format
        if '/s3' in s3_endpoint:
            base_endpoint = s3_endpoint.replace('/storage/v1/s3', '')
            public_url = f"{base_endpoint}/storage/v1/object/public/{bucket_name}/{object_path}"
        else:
            public_url = f"{s3_endpoint}/{bucket_name}/{object_path}"

        # Generate a presigned URL as fallback URL
        try:
            presigned_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_path},
                ExpiresIn=604800  # Valid for 7 days
            )
            final_url = presigned_url
        except Exception:
            final_url = public_url

        logger.info(f"Successfully uploaded PDF to Supabase. Storage path: '{full_storage_path}'")
        return full_storage_path, final_url

    except Exception as e:
        logger.error(f"Failed to upload receipt to Supabase Storage: {e}", exc_info=True)
        raise e

def upload_general_logo_to_supabase():
    """
    Uploads static/images/main_logo.png to Supabase Storage bucket 'payment-receipts' under key 'general/main_logo.png'.
    Returns (storage_path, public_url).
    """
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'main_logo.png')
    if not os.path.exists(logo_path):
        logger.warning(f"Logo path not found at '{logo_path}'")
        return None, None

    bucket_name = os.getenv('SUPABASE_RECEIPTS_BUCKET', 'payment-receipts').strip()
    object_path = "general/main_logo.png"
    full_storage_path = f"{bucket_name}/{object_path}"

    try:
        s3 = get_s3_client()
        ensure_bucket_exists(s3, bucket_name)

        with open(logo_path, 'rb') as f:
            logo_bytes = f.read()

        s3.put_object(
            Bucket=bucket_name,
            Key=object_path,
            Body=logo_bytes,
            ContentType='image/png',
            CacheControl='public, max-age=31536000'
        )

        s3_endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', '') or os.getenv('SUPABASE_STORAGE_S3_ENDPOINT', '').strip()
        if '/s3' in s3_endpoint:
            base_endpoint = s3_endpoint.replace('/storage/v1/s3', '')
            public_url = f"{base_endpoint}/storage/v1/object/public/{bucket_name}/{object_path}"
        else:
            public_url = f"{s3_endpoint}/{bucket_name}/{object_path}"

        logger.info(f"Uploaded main_logo.png to Supabase Storage: '{full_storage_path}'")
        return full_storage_path, public_url
    except Exception as e:
        logger.error(f"Failed to upload logo to Supabase Storage: {e}", exc_info=True)
        return None, None

def delete_receipt_from_supabase(receipt_path):
    """
    Deletes PDF receipt file from Supabase Storage bucket given its full storage path or object key.
    """
    if not receipt_path:
        return
    bucket_name = os.getenv('SUPABASE_RECEIPTS_BUCKET', 'payment-receipts').strip()
    object_key = receipt_path.split('/', 1)[1] if '/' in receipt_path else receipt_path

    try:
        s3 = get_s3_client()
        logger.info(f"Deleting receipt PDF '{object_key}' from Supabase bucket '{bucket_name}'...")
        s3.delete_object(Bucket=bucket_name, Key=object_key)
        logger.info(f"Successfully deleted receipt PDF '{object_key}' from Supabase Storage.")
    except Exception as e:
        logger.warning(f"Could not delete receipt PDF '{object_key}' from Supabase Storage: {e}")
