import requests
from PIL import Image
from io import BytesIO
import base64
from lambda_handler import lambda_handler  # assuming your main file is named image_processor.py

def test_lambda_handler():
    # Define the image URL
    image_url = "https://cdn1.sportngin.com/attachments/photo/8993/1181/come-on-lets-party_large.jpg"

    # Download the image
    response = requests.get(image_url)
    
    # Open the image with PIL
    image = Image.open(BytesIO(response.content))

    # Convert the image to base64
    base64_image = base64.b64encode(response.content).decode('utf-8')

    # Define a test event
    event = {
        'body': base64_image
    }

    # Call the lambda handler
    result = lambda_handler(event, None)

    # Extract the text from the body response
    text = result['body']
    
    # Lower case the text
    text = text.lower()
    print(text,'text')
    # Check if 'party' is in the text
    assert 'party' in text, "Test failed: 'party' not found in the response text"

if __name__ == "__main__":
    print(test_lambda_handler())

