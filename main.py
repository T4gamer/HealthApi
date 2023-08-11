
from flask import Flask
from flask_restful import Resource, Api
from firebase_admin import credentials  , initialize_app ,firestore
import datetime
cred = credentials.Certificate("health-app-9b596-firebase-adminsdk-4aghe-f22ab4a45f.json")
initialize_app(cred)

app = Flask(__name__)
api = Api(app)

records_collection = firestore.client().collection("records")
users_collection = firestore.client().collection('users')

def check_mac(apiMac):
    document = users_collection.where("device", "==", apiMac).get()
    if len(document) > 0:
        return document[0]
    else:
        return None
    

class DeviceApi(Resource):
    def get(self,mac,bpm,temp,o2):
        user = check_mac(mac)
        if user.id:
            if user.get("recive") == False:
                self.prev_recive = user.get("recive")
                return {"error":"can't send data unil test begins"}
            if user.get("recive") == self.prev_recive:
                timestamp = datetime.datetime.now()
                new_document = {
                    "bpm": bpm,
                    "temp": temp,
                    "oxg": o2,
                    "date": timestamp,
                    "user": user.id,
                }
                records_collection.add(new_document)
            else:
                user = users_collection.get()
            return {"mac":mac,"bpm":bpm,"temp":temp,"o2":o2}
        else:
            return{"error":"no user with device {}".format(mac)}
    
api.add_resource(DeviceApi, '/<string:mac>/<int:bpm>/<int:temp>/<int:o2>/')


if __name__ == '__main__':
    app.run(debug=True)
