from flask import Flask, redirect, url_for,session,request, render_template, abort
import responses
import os, sys
from azure.core.exceptions import ResourceNotFoundError
from azure.ai.formrecognizer import FormRecognizerClient
from azure.ai.formrecognizer import FormTrainingClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__
from msrest.authentication import CognitiveServicesCredentials

from azure.cognitiveservices.vision.face import FaceClient
from shutil import copyfile
from datetime import date
import base64
from io import BytesIO
from PIL import Image
import pyodbc

import configparser


# Define a flask app
app = Flask(__name__)

class Data: 
    def __init__(self):
        self.id_image_path = None
        self.selfie_image = None
        self.not_underage = False
        self.username = ""
        self.image_not_uploaded = True

data = Data()

CONFIDENCE_THRESHOLD = 0.5


# Route the user to the homepage
@app.route('/', methods = ['GET'])
def home():
    return render_template('index.html')

# Route to about page
@app.route('/about', methods = ['GET'])
def about():
    return render_template('about_planner.html')

@app.route("/api/upload_id", methods=["POST"])
def id_img_handler():
    """
    This routine handles ID images that are sent to the server...
    The id_image variable expects a Base64 encoded image...
    """
    print("id_img_handler has been called!")
    print("request:", request.files)
    
    image = request.files["id_image"]
    save_loc = os.path.join(app.config["UPLOAD_FOLDER"], "tmp.png")
    with open(save_loc, "wb"):
        image.save(save_loc)

    store_custid_image_and_path("wmt_user8", save_loc)

    id_api_endpoint = "https://formrecognizeid.cognitiveservices.azure.com/"

    dob_result = extract_dob(id_api_endpoint, save_loc)

    if dob_result:
        # TODO:
        # store the user id and the image into the DB
        print("User is older than 21!")
        data.id_image_path = save_loc
        data.not_underage = True
        data.image_not_uploaded = False

        return responses.get_http_200()
    else:
        print("User is NOT older than 21... :(")
        return responses.get_http_200()


@app.route("/api/upload_selfie", methods=["POST"])
def selfie_img_handler():
    """
    Handle selfie images that are sent to the server... 
    """
    # selfie_image = request.form["selfie_image"]
    print("Selfie image handler has been called!")
    
    if request.method == 'POST':
        file = request.form['file'].split(",")[1]
        im = Image.open(BytesIO(base64.b64decode(file)))
        im.save('./temp_uploads/selfie.png', 'PNG')
    # Load image from local into stream ->(selfie.png)

    # target_image_id = target_faces2[0].face_id
    # data.selfie_image = target_image_id

    # TODO: write 
    # compare this image with the ID image
    # use blob URL to obtain ID image
    # compare faceids
    # verify faces using direct url 

    IMAGE_BASE_URL = "https://wmtcustinfo.blob.core.windows.net/wmtcustinfo/"
    ENDPOINT = "https://face-wmt-hackathon.cognitiveservices.azure.com/"
    face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(app.FACE_KEY))


    source_image_file_name1 = IMAGE_BASE_URL + "wmt_user8" + "_user_identification_card.jpg" 

    print("source_iage_file_name1:", source_image_file_name1)
    source_faces1 = face_client.face.detect_with_url(source_image_file_name1, detection_model='detection_03')
    source_image1_id = source_faces1[0].face_id

    target_image_file_name = open('./temp_uploads/selfie.png', 'r+b')
    target_faces2 = face_client.face.detect_with_stream(target_image_file_name, detection_model='detection_03')
    target_face_id = target_faces2[0].face_id

    result = face_client.face.verify_face_to_face(source_image1_id, target_face_id)
    print("result:", result)

    confidence = result.is_identical
    if confidence >= CONFIDENCE_THRESHOLD:
        return responses.get_http_200()

    print("The images do not match.")
    abort(404)
    

    
@app.route("/api/login", methods=["POST"])
def login_handler():
    """
    Handle what happens once the user logs in... 
    """

    username = request.form["username"]
    data.username = username
    print("login handler called successfully")
    print("username:", username)

    # TODO: 
    # store temporarily the image and the username in the backend...
    # obtain the user image and the user 
    # persist the username and the image to the db
    # at this stage, the user image should be populated...
    return responses.get_http_200()


def extract_dob(endpoint,id_proof):
    """
    Written by @lokaadithireddy
    -- param endpoint: the azure api endpoint
    -- param id_proof: a string that represents the location of the id
                       in order for this to work, we need to ensure that the image is saved locally
                       first 
    """
    form_recognizer_client = FormRecognizerClient(endpoint=endpoint, credential=AzureKeyCredential(app.OCR_KEY))
    with open(id_proof, "rb") as f:
        poller = form_recognizer_client.begin_recognize_identity_documents(identity_document=f)
    id_documents = poller.result()
    for idx, id_document in enumerate(id_documents):
        print("--------Recognizing ID document #{}--------".format(idx+1))
        dob = id_document.fields.get("DateOfBirth")
    if dob:
        print("Date of Birth: {} has confidence: {}".format(dob.value, dob.confidence))
        born = dob.value
        today = date.today()
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return age >= 21
    else:
        print('Issue with dob parsing')


def store_custid_image_and_path(username: str, save_loc:str):
    #get the username and save_loc path , insert a record in the db , path , and store image with renamed in blob storage
    conn_server = 'gtech.database.windows.net'
    conn_database = 'customers'
    conn_username = 'rootadmin'
    conn_password = 'DoesItReallyMatter199'
    conn_driver = '{ODBC Driver 17 for SQL Server}'

    # store image in blob storage
    os.environ["AZURE_STORAGE_CONNECTION_STRING"] = "DefaultEndpointsProtocol=https;AccountName=wmtcustinfo;AccountKey=+42Znv+7y6OQGNrgrnLqWnVwmq3S5lEGY1hS0zaUm7ayEzCgI0ZuFd89/G9e1BPg6uNYWFXqJNG35TflTRQCEw==;EndpointSuffix=core.windows.net"
    connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    container_name="wmtcustinfo"
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    base_dir = os.path.dirname(save_loc)
    user_id_filename = F'{username}_user_identification_card.jpg'
    upload_file_path = base_dir + "/" + user_id_filename
    print("save_loc = {0}".format(save_loc))
    print("upload_file_path = {0}".format(upload_file_path))
    print("copying customer id to new file path")
    copyfile(save_loc, upload_file_path)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=user_id_filename)
    # Upload the created file
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data)
    print("upload complete ")
    blob_url="https://wmtcustinfo.blob.core.windows.net/wmtcustinfo/" + user_id_filename

    try:
        with pyodbc.connect('DRIVER=' + conn_driver + ';SERVER=tcp:' + conn_server + ';PORT=1433;DATABASE=' + conn_database + ';UID=' + conn_username + ';PWD=' + conn_password) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""insert into dbo.wmt_cust_account (username,id,dob,userid_photo_path) values ('{0}' , null,null , '{1}') """.format(username, blob_url))
    except:
        print("Unexpected error:", sys.exc_info())
        exit(1)

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("properties.ini")
    app.OCR_KEY = config["KEYS"]["ocr_key"]
    app.FACE_KEY = config["KEYS"]["face_key"]
    app.config["UPLOAD_FOLDER"] = "temp_uploads/"
    app.run(debug=True, port=10061)



