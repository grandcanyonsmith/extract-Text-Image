import boto3
import base64
import uuid
import os

def process_image(image_binary_data):
    # Initialize Textract client
    textract = boto3.client('textract', region_name='us-west-2')

    # Call Textract to extract text
    response = textract.detect_document_text(Document={'Bytes': image_binary_data})

    # Process and return the response
    text = ""
    for item in response['Blocks']:
        if item['BlockType'] == 'LINE':
            text += item['Text'] + '\n'
    print(text,'text')
    return text

def lambda_handler(event, context):
    try:
        # Initialize S3 client
        s3 = boto3.client('s3', region_name='us-west-2')

        # Define S3 bucket
        bucket = 'publicbucketszoomrecord'

        # Get base64 image from the POST request body
        base64_image = event['body']

        # Decode base64 image
        try:
            image_binary_data = base64.b64decode(base64_image)
        except Exception as e:
            print(f"Error decoding base64 image: {e}")
            return {'statusCode': 500, 'body': f"Error decoding base64 image: {e}"}

        # Generate a unique file name
        file_name = os.path.join('/tmp', str(uuid.uuid4()) + '.png')

        # Write the image to a file in the /tmp directory
        with open(file_name, 'wb') as file:
            file.write(image_binary_data)

        print(f"Image saved as {file_name}.")

        # Upload the image to S3
        try:
            with open(file_name, 'rb') as file:
                s3.put_object(Body=file, Bucket=bucket, Key=os.path.basename(file_name), ContentType='image/png')
        except Exception as e:
            print(f"Error uploading image to S3: {e}")
            return {'statusCode': 500, 'body': f"Error uploading image to S3: {e}"}

        # Process the image with Textract
        try:
            extracted_text = process_image(image_binary_data)
        except Exception as e:
            print(f"Error processing image with Textract: {e}")
            return {'statusCode': 500, 'body': f"Error processing image with Textract: {e}"}

        # Optionally, clean up the image from /tmp if you're concerned about storage
        try:
            os.remove(file_name)
        except Exception as e:
            print(f"Warning: Could not remove temporary file {file_name}: {e}")

        return {'statusCode': 200, 'body': extracted_text}

    except Exception as e:
        print(e)
        return {'statusCode': 500, 'body': str(e)}