import boto3
import base64
import uuid
import os
import logging
from botocore.exceptions import BotoCoreError, ClientError

class ImageProcessor:
    def __init__(self, s3_bucket, aws_region):
        self.s3 = boto3.client('s3', region_name=aws_region)
        self.textract = boto3.client('textract', region_name=aws_region)
        self.bucket = s3_bucket
        self.logger = logging.getLogger(__name__)

    def decode_image(self, base64_image):
        try:
            return base64.b64decode(base64_image)
        except Exception as e:
            self.logger.error(f"Error decoding base64 image: {e}")
            raise ValueError("Invalid base64 image") from e

    def save_image(self, image_binary_data):
        file_name = os.path.join('/tmp', str(uuid.uuid4()) + '.png')
        try:
            with open(file_name, 'wb') as file:
                file.write(image_binary_data)
        except Exception as e:
            self.logger.error(f"Error saving image: {e}")
            raise IOError("Error saving image to disk") from e
        return file_name

    def upload_image_to_s3(self, file_name):
        try:
            with open(file_name, 'rb') as file:
                self.s3.put_object(Body=file, Bucket=self.bucket, Key=os.path.basename(file_name), ContentType='image/png')
        except (BotoCoreError, ClientError) as e:
            self.logger.error(f"Error uploading image to S3: {e}")
            raise Exception("Error uploading image to S3") from e

    def process_image(self, image_binary_data):
        try:
            response = self.textract.detect_document_text(Document={'Bytes': image_binary_data})
            return '\n'.join(item['Text'] for item in response['Blocks'] if item['BlockType'] == 'LINE')
        except (BotoCoreError, ClientError) as e:
            self.logger.error(f"Error processing image with Textract: {e}")
            raise Exception("Error processing image with Textract") from e

    def cleanup(self, file_name):
        try:
            os.remove(file_name)
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            raise IOError("Error during cleanup") from e

def lambda_handler(event, context):
    aws_region = os.getenv('AWS_REGION', 'us-west-2')
    s3_bucket = os.getenv('S3_BUCKET_NAME', 'publicbucketszoomrecord')
    processor = ImageProcessor(s3_bucket, aws_region)

    try:
        base64_image = event['body']
        image_binary_data = processor.decode_image(base64_image)
        file_name = processor.save_image(image_binary_data)
        processor.upload_image_to_s3(file_name)
        extracted_text = processor.process_image(image_binary_data)
        processor.cleanup(file_name)
        return {'statusCode': 200, 'body': extracted_text}
    except Exception as e:
        return {'statusCode': 500, 'body': str(e)}