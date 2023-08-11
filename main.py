
from flask import Flask ,request,g
from flask_restful import Resource, Api
from firebase_admin import credentials  , initialize_app ,firestore,db
import datetime
from time import time
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

save_list = {}


class RateLimitMiddleware:
    def __init__(self, app, limit=1):
        self.app = app
        self.limit = limit
        self.clients = {}

    def __call__(self, environ, start_response):
        client_id = environ.get('HTTP_X_REAL_IP', environ.get('REMOTE_ADDR'))
        if client_id:
            last_request = self.clients.get(client_id)
            if last_request and time() - last_request < self.limit:
                response = app.response_class(
                    response='Too Many Requests',
                    status=429,
                    mimetype='application/json'
                )
                return response(environ, start_response)
            else:
                self.clients[client_id] = time()
        return self.app(environ, start_response)

app.wsgi_app = RateLimitMiddleware(app.wsgi_app)



class DeviceApi(Resource):
    def get(self,mac,bpm,temp,o2):
        user = check_mac(mac)
        if user.id:
            save_list[mac] = user.get("recive")
            if save_list[mac] == False:
                try:
                    if save_list[f"last{mac}"] == True:
                        timestamp = datetime.datetime.now()
                        new_document = {
                            "bpm": bpm,
                            "temp": temp,
                            "oxg": o2,
                            "date": timestamp,
                            "user": user.id,
                        }
                        records_collection.add(new_document)
                        save_list[f"last{mac}"] = save_list[mac]
                        return {"success":"record added"}
                except Exception:
                    pass
                save_list[f"last{mac}"] = save_list[mac]
                return {"error":"can't send data unil test begins"}
            else:
                doc_ref = users_collection.document(user.id)
                doc_ref.update({"temp":temp})
                doc_ref.update({"bpm":bpm})
                doc_ref.update({"oxg":o2})
                save_list[f"last{mac}"] = save_list[mac]
            return {"mac":mac,"bpm":bpm,"temp":temp,"o2":o2}
        else:
            return{"error":"no user with device {}".format(mac)}
api.add_resource(DeviceApi, '/<string:mac>/<int:bpm>/<int:temp>/<int:o2>/')


if __name__ == '__main__':
    app.run(debug=True)
