from flask import Flask, render_template, request
import os
from uuid import uuid4
from threading import Thread
import datetime
import json

from api import API_EmailSender, API_ImageClassifier, API_ImageStorage, API_ImageColourizer, API_DataStorage, get_image_metadata

app = Flask(__name__)
URL = "image-forensics.herokuapp.com"

@app.route('/')
def index():
    """
    Renders the default page for uploading images
    :return: index.html template
    """
    return render_template('index.html')

@app.route('/result/<uuid>')
def result(uuid):
    """
    Renders the results page with the analysis JSON data
    :param uuid: The UUID of the results page
    :return: result.html template, or 404.html on error
    """
    result = load_result(uuid)
    if result is None: # UUID wasn't found, throw 404
        return render_template('404.html')

    return render_template('result.html', filename=result["filename"],
                           details=result["exif"],
                           classification=result["labels"],
                           before=result["before"],
                           after=result["after"],
                           timestamp=result["timestamp"])



@app.route('/upload', methods=['POST'])
def upload():
    """
    Uploads the image from the form data and starts the analysis in a thread
    :return: string 'SUCCESS' on success, 'FAIL' on failure
    """
    # Ensure the user has added a file and email
    try:
        file = request.files['filedata']
        orig_filename = file.filename
        email = request.form['email']
    except:
        return 'FAIL'
    # Otherwise, save the file
    new_filename = str(uuid4())
    file.save(os.path.join('uploads', f'{new_filename}.jpg'))

    # Create a worker thread to do the API calls
    worker = Thread(target=run_worker, args=(new_filename, email, orig_filename))
    worker.start()
    return 'SUCCESS'

def get_timestamp():
    """ Returns a timestamp similar to 'February 14, 2019 at 5:46 PM'
    """
    now = datetime.datetime.now()
    return now.strftime("%B %d, %Y at %I:%M %p")

def load_result(uuid, retry=False):
    """ Given a UUID, returns the corresponding result JSON.
        Automatically checks local storage and Firebase external storage
        Returns: JSON on success, None on failure
    """
    json_file = os.path.join('json', str(uuid)) # json/uuid
    json_path = f'{json_file}.json' # Same name, + .json

    # Check local cache first for JSON file
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Failsafe: if this is our second attempt, bail out
        if retry:
            return None

        # File wasn't found locally; redownload and rerun
        try:
            print("JSON wasn't found locally; downloading from DataStorage")
            API_DataStorage.download(json_file, json_path)
            return load_result(uuid, retry=True)
        except Exception:
            print("Unable to retrieve JSON from DataStorage.")
            return None


def run_worker(uuid, email, filename):
    """
    Runs the analysis in a thread:
        1. Upload image to ImageStorage
        2. Classify image features
        3. Retrieve image metadata
        3. Colourize image
        4. Upload colourized image to ImageStorage
        5. Collates data, creates JSON
        6. Uploads JSON to DataStorage
        7. Sends an email notifiying the user that the process is completed

    :param uuid: Image file UUID
    :param email: Email for notification
    :param filename: Original filename of the image
    :return:
    """
    jpg_path = os.path.join('uploads', f'{uuid}.jpg')
    path_orig = f'orig-{uuid}'
    path_col = f'col-{uuid}'

    # Upload image to imagestore
    API_ImageStorage.upload(jpg_path, path_orig)
    original_image = API_ImageStorage.get(path_orig).url

    # Classify image
    labels = API_ImageClassifier.classify(original_image)
    label_dict = {key.title(): round(val*100, 2) for key, val in labels} # Convert list of tuples to dictionary

    # Retrieve image metadata
    exif = get_image_metadata(jpg_path)

    # Colourize image
    enhanced = API_ImageColourizer.enhance(original_image)

    # Store colourized image
    API_ImageStorage.upload(enhanced, path_col)
    colour_image = API_ImageStorage.get(path_col).url

    # Collate data
    json_data = {
        "filename": filename,
        "before": original_image,
        "after": colour_image,
        "labels": label_dict,
        "exif": exif,
        "timestamp": get_timestamp()
    }

    # Create datafile
    json_path = os.path.join('json', f'{uuid}.json')
    with open(json_path, "w") as f:
        json.dump(json_data, f)

    # Store the datafile on Firebase
    API_DataStorage.put(json_path, f'json/{uuid}')

    # Notify user of image results
    API_EmailSender.send(mailfrom=f"forensics@{URL}", mailto=email, subject="Results", content=f"Please see the results: https://{URL}/result/{uuid}")


if __name__ == '__main__':
    app.run() # Start the server