import json

def get_http_200():
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
