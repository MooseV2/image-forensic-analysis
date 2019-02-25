import requests
import pyrebase
import cloudinary
import cloudinary.uploader as uploader
import sendgrid
from sendgrid.helpers.mail import *
import PIL, PIL.Image, PIL.ExifTags

class ImageClassifier:
    """
    ImageClassifier
    Uses the Clarifai "General" image classifier to classify images
    """
    def __init__(self, api_key):
        self.headers = {"Authorization": f"Key {api_key}"}

        # General Clarifai image classifier endpoint
        self.url = "https://api.clarifai.com/v2/models/aaa03c23b3724a16a56b629203edc62c/versions/aa7f35c01e0642fda5cf400f543e7c40/outputs"

    def classify(self, image_url, results=8):
        data = {"inputs": [{"data": {"image": {"url": image_url}}}]}
        response = requests.post(self.url, json=data, headers=self.headers)
        try:
            output_data = response.json()["outputs"][0]["data"]["concepts"]
            output_labels = [(item["name"], item["value"]) for item in output_data]
            return output_labels[:results]
        except Exception:
            return False

class ImageColourizer:
    """
    ImageColourizer
    Uses the DeepAI API to colourize images
    """
    def __init__(self, api_key):
        self.url = "https://api.deepai.org/api/colorizer"
        self.headers = {'api-key': api_key}
    def enhance(self, image_url):
        data={'image': image_url}
        response = requests.post(self.url, data=data, headers=self.headers)
        try:
            result = response.json()
            return result["output_url"]
        except Exception:
            return False

class DataStorage:
    """
    DataStorage
    Uses the FireBase API to store/retrieve files
    """
    def __init__(self, api_config):
        firebase = pyrebase.initialize_app(api_config)
        self.storage = firebase.storage()

    def put(self, localfile, remotefile):
        self.storage.child(remotefile).put(localfile)

    def get_url(self, remotefile):
        return self.storage.child(remotefile).get_url(None)

    def download(self, remotefile, localfile):
        return self.storage.child(remotefile).download(localfile)

class EmailSender:
    """
    EmailSender
    Sends an email using the SendGrid API
    """
    def __init__(self, api_key):
        self.sender = sendgrid.SendGridAPIClient(apikey=api_key)

    def send(self, mailfrom="test@example.com",
             mailto="test@example.com",
             subject="Test",
             content="Test content",
             ctype="text/plain"):

        from_email = Email(mailfrom)
        to_email = Email(mailto)
        content = Content(ctype, content)
        mail = Mail(from_email, subject, to_email, content)
        response = self.sender.client.mail.send.post(request_body=mail.get())

class ImageStorage:
    """
    ImageStorage
    Stores and retrieves images through the Cloudinary API
    """
    def __init__(self, api_config):
        cloudinary.config(**api_config)

    def upload(self, file, id):
        return uploader.upload(file, public_id=id)

    def get(self, id):
        return cloudinary.CloudinaryImage(id)

def get_image_metadata(path):
    """
    Given an image path, returns the image's EXIF information
    :param path: Image path
    :return: dict of EXIF information
    """
    exif = {}
    try:
        image = PIL.Image.open(path)
        exif = {
            PIL.ExifTags.TAGS[k]: str(v)
            for k, v in image._getexif().items()
            if k in PIL.ExifTags.TAGS
        }
    except:
        print("Unable to retrieve EXIF")
    return exif


from api_keys import key_email_sender,\
    key_image_classifier,\
    key_image_enhancer,\
    config_imagestorage,\
    config_datastorage


# Exports
API_EmailSender = EmailSender(key_email_sender)
API_ImageColourizer = ImageColourizer(key_image_enhancer)
API_ImageClassifier = ImageClassifier(key_image_classifier)
API_ImageStorage = ImageStorage(config_imagestorage)
API_DataStorage = DataStorage(config_datastorage)