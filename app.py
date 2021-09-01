from flask import Flask, redirect, url_for,session,request, render_template
import responses
import os
from azure.core.exceptions import ResourceNotFoundError
from azure.ai.formrecognizer import FormRecognizerClient
from azure.ai.formrecognizer import FormTrainingClient
from azure.core.credentials import AzureKeyCredential
from datetime import date
import base64
from io import BytesIO
from PIL import Image

# Define a flask app
app = Flask(__name__)
app.secret_key='trafficaid'


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

    id_api_endpoint = "https://formrecognizeid.cognitiveservices.azure.com/"

    dob_result = extract_dob(id_api_endpoint, save_loc)

    if dob_result:
        # TODO:
        # store the user id and the image into the DB
        print("User is older than 21!")
        data.id_image_path = save_loc
        data.not_underage = True
        data.image_not_uploaded = False

        return responses.get_http_200(message="true")
    else:
        print("User is NOT older than 21... :(")
        return responses.get_http_200(message="false")


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

    # target_image_file_name = open('./temp_uploads/image.png', 'r+b')
    # target_faces2= face_client.face.detect_with_stream(target_image_file_name, detection_model='detection_03')
    # target_image_id = target_faces2[0].face_id
    # data.selfie_image = target_image_id
    
    # TODO: write 
    # compare this image with the ID image

    return render_template('index.html')
    

    
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
    form_recognizer_client = FormRecognizerClient(endpoint=endpoint, credential=AzureKeyCredential(app.azure_secret))
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


# Route to Data Analysis Page
@app.route('/data', methods = ['GET','POST'])
def data():
    #my_map = getFoliumdata()
    #return my_map._repr_html_()
    session.clear()
    if request.method == 'POST':
        stationid=request.form.get('station')
        Fwy=request.form.get('fwy')
        startDate=request.form.get('filterDate')
        if Fwy=="Select a Freeway":
            Fwy=""
        session['stationid']=stationid
        session['Fwy']=Fwy
        if startDate!="":
            startDate=startDate+" 00:00:00"
        session['startDate']=startDate
        redirect(url_for('getFoliumMap'))
    stationid=session.get('stationid')
    Fwy=session.get('Fwy')
    startDate=session.get('startDate')
    if not stationid:
        stationid=""
    if not Fwy:
        Fwy=""
    if not startDate:
        startDate='2018-01-01 00:00:00'
    if (stationid=="") & (Fwy==""):
        Fwy="280"
    details=[stationid,Fwy,startDate[0:10]]
    liststatus=['Select a Freeway','101','280','680','880']
    return render_template('dataAnalysis.html',details=details,liststatus=liststatus)

@app.route("/simple_chart")
def chart():
    stationid=session.get('stationid')
    Fwy=session.get('Fwy')
    startDate=session.get('startDate')
    if not stationid:
        stationid=""
    if not Fwy:
        Fwy=""
    if not startDate:
        startDate='2018-01-01 00:00:00'
    if (stationid=="") & (Fwy==""):
        Fwy="280"
    bar = charts.create_plot(stationid,Fwy,startDate)
    return render_template('chart.html', plot=bar)

@app.route("/dual_chart")
def dual_chart():
    stationid=session.get('stationid')
    Fwy=session.get('Fwy')
    startDate=session.get('startDate')
    if not stationid:
        stationid=""
    if not Fwy:
        Fwy=""
    if not startDate:
        startDate='2018-01-01 00:00:00'
    if (stationid=="") & (Fwy==""):
        Fwy="280"
    bar = charts.create_dual_plot(stationid,Fwy,startDate)
    return render_template('dual_chart.html', plot=bar)

@app.route("/weather_chart")
def weather_chart():
    stationid=session.get('stationid')
    Fwy=session.get('Fwy')
    startDate=session.get('startDate')
    if not stationid:
        stationid=""
    if not Fwy:
        Fwy=""
    if not startDate:
        startDate='2018-01-01 00:00:00'
    if (stationid=="") & (Fwy==""):
        Fwy="280"
    weather_details=charts.create_weather_chart(stationid,Fwy,startDate)
    return render_template('weather_chart.html',weather_details=weather_details)

# Route to model page
@app.route('/model', methods = ['GET'])
def model():
    return render_template('model.html')
# Route to prediction page

@app.route('/prediction', methods = ['GET','POST'])
def prediction(): 
    #session['Freeway'] = request.form.get("fwy")
    # if(session.get('avgocc')):
    #     avgocc = session.get('avgocc')
    #     print(avgocc)
    # if request.method == 'POST':
    Fwy = request.form.get('fwy')
    print(Fwy)
    timetak, avgocc, avgspeed, avgvisibility, avgwindspeed, avgprecipitation, incidentcount = getFoliumMapPred(Fwy)
    if(timetak!=0):
        timetaklow = str(float(timetak)-8)
        timetakhigh = str(float(timetak)+8)
    else:
        timetaklow = 0
        timetakhigh = 0
    return render_template('traffic_prediction.html',timetaklow=timetaklow,timetakhigh=timetakhigh, avgocc=avgocc, avgspeed=avgspeed, avgvisibility=avgvisibility, avgwindspeed=avgwindspeed, avgprecipitation=avgprecipitation, incidentcount=incidentcount)

@app.route('/getFoliumMap')
def getFoliumMap():

    stationid=session.get('stationid')
    Fwy=session.get('Fwy')
    startDate=session.get('startDate')
    if not stationid:
        stationid=""
    if not Fwy:
        Fwy=""
    if not startDate:
        startDate='2018-01-01 00:00:00'
    if (stationid=="") & (Fwy==""):
        Fwy="280"
    print("Session",stationid,Fwy,startDate)
    my_map=charts.get_folium_map(stationid,Fwy,startDate)
    #my_map.save('index.html')
    return my_map._repr_html_()


@app.route('/getFoliumMapPred', methods = ['GET','POST'])
def getFoliumMapPred(Fwy):
    # Fwy = request.form.get("fwy")
    print("Here")
    if(Fwy!=None):
        my_map,timetak,avgocc, avgspeed, avgvisibility, avgwindspeed, avgprecipitation, incidentcount = realtime.getreal(Fwy)
    else:
        my_map=realtime.popdum()
        timetak = 0
        avgocc = 0
        avgspeed = 0
        avgvisibility = 0
        avgwindspeed = 0
        avgprecipitation = 0
        incidentcount = 0 

    return timetak, avgocc, avgspeed, avgvisibility, avgwindspeed, avgprecipitation, incidentcount    
        # return my_map._repr_html_()
    # redirect(url_for('prediction'))
    #return render_template('index.html')


class Data: 
    def __init__(self):
        self.id_image_path = None
        self.selfie_image = None
        self.not_underage = False
        self.username = ""
        self.image_not_uploaded = True

def get_secret_key():
    with open("keys.txt") as f:
        key = f.read()

    print(key[key.find("=")+1:])
    return key[key.find("=")+1:]

if __name__ == '__main__':
    app.secret_key="casdfnjakwhejfwefjkwnemwh87h"
    app.azure_secret = get_secret_key()
    app.config["UPLOAD_FOLDER"] = "temp_uploads/"
    app.run(debug=True, port=10061)
    data = Data()



