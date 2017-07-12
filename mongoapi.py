from flask import Flask
from flask import jsonify
from flask import request
from flask import abort
from flask_pymongo import PyMongo
from pymongo import GEO2D
from bson.son import SON

app = Flask(__name__)
with app.app_context():
  app.config['MONGO_DBNAME'] = 'mycrowdcharger'
  app.config['MONGO_URI'] = 'mongodb://spyros.hopto.org:27017/mycrowdcharger'
  mongo = PyMongo(app)
  mongo.db.devices.create_index([("loc", GEO2D)])


@app.route('/device', methods=['GET'])
def get_all_devices():
  device = mongo.db.devices
  output = []
  for s in device.find():
    output.append({'name' : s['name'], 'loc' : s['loc'], "battery_level": s['battery_level'], 
      "contributions": s['contributions'], "nickname": s['nickname']})
  return jsonify({'result' : output})

@app.route('/device/<name>', methods=['GET'])
def get_one_device(name):
  device = mongo.db.devices
  s = device.find_one({'name' : name})
  if s:
    output = {'name' : s['name'], 'loc' : s['loc'], "battery_level": s['battery_level'], 
      "contributions": s['contributions'], "nickname": s['nickname']}
  else:
    output = "No such name"
  return jsonify({'result' : output})

@app.route('/register', methods=['POST'])
def add_device():
  #mongo.db.devices.create_index([("loc", GEO2D)])
  device = mongo.db.devices
  name = request.json['name']
  loc = request.json['loc']
  nickname = request.json['nickname']
  s = device.find_one({'name' : name})
  if s:
    output = "device already registered"
  else:
    battery_level = request.json['battery_level']
    device_id = device.insert({'name': name, 'battery_level': battery_level, 
      'loc' : loc, "contributions": 1, "nickname": nickname })
    new_device = device.find_one({'_id': device_id })
    output = {'name' : new_device['name'], 'loc' : new_device['loc'], "battery_level": new_device['battery_level'], 
        "contributions": new_device['contributions'], "nickname": new_device['nickname']}
  return jsonify({'result' : output})

@app.route('/refresh', methods=['POST'])
def refresh_device():
  device = mongo.db.devices
  name = request.json['name']
  loc = request.json['loc']

  battery_level = request.json['battery_level']

  saved_device = device.find_one({'name' : name})
  if saved_device is not None:
    saved_device['loc'] = loc
    saved_device['battery_level'] = battery_level
    device.save(saved_device)
    new_device = device.find_one({'_id': saved_device['_id'] })
    output = {'name' : new_device['name'], 'loc' : new_device['loc'], "battery_level": new_device['battery_level'], 
        "contributions": new_device['contributions'], "nickname": new_device['nickname']}
    return jsonify({'result' : output})
  else:
    abort(404)

@app.route('/sendbattery', methods=['POST'])
def send_battery():
  device = mongo.db.devices
 
  sender = request.json['sender']['name']
  battery = int(request.json['sender']['battery'])
  recipient = request.json['recipient']['name']
  
  senderdoc = device.find_one({'name' : sender})
  recipientdoc = device.find_one({'name': recipient})
  if senderdoc is None:
    abort(404)
  if recipient is None:
    abort(404)
  
  sender_battery_level = int(senderdoc['battery_level'])
  recipient_battery_level = int(recipientdoc['battery_level'])
  if sender_battery_level < battery:
    abort(400)
  senderdoc['battery_level'] = sender_battery_level - battery
  senderdoc['contributions'] = int(senderdoc['contributions']) + 1
  if recipient_battery_level + battery <=100:
    recipientdoc['battery_level'] = recipient_battery_level + battery
  else:
    abort(400)
  device.save(senderdoc)
  device.save(recipientdoc)
  
  updated_sender = device.find_one({'_id' : senderdoc['_id']})
  updated_recipient = device.find_one({'_id' : recipientdoc['_id']})

  if updated_sender is not None and updated_recipient is not None:
     sender_output = {'name' : updated_sender['name'], 'loc' : updated_sender['loc'], "battery_level": updated_sender['battery_level'], 
        "contributions": updated_sender['contributions'], "nickname": updated_sender['nickname']}
     recipient_output = {'name' : updated_recipient['name'], 'loc' : updated_recipient['loc'], "battery_level": updated_recipient['battery_level'], 
        "contributions": updated_recipient['contributions'], "nickname": updated_recipient['nickname']}
     return jsonify({'result_sender' : sender_output, 'result_recipient': recipient_output})
  else:
    abort(500)

@app.route('/nearby/<lon>/<lat>', methods=['GET'])
def get_nearby_devices(lon, lat):
  device = mongo.db.devices
  loc = [float(lon), float(lat)]
  query = {"loc": SON([("$near", loc), ("$maxDistance", 0.1)])}
  #query = {"loc": SON([("$near", loc)])}
  output = []
  for doc in device.find(query).limit(10):
    output.append({'name' : doc['name'], 'loc' : doc['loc'], "battery_level": doc['battery_level'], 
      "contributions": doc['contributions'], "nickname": doc['nickname']})
  return jsonify({'result' : output})

@app.route('/getnearesttodevice/<name>', methods=['GET'])
def get_nearby_devices_by_device_name(name):
  device = mongo.db.devices
  new_device = device.find_one({'name': name })
  if new_device is None:
    abort(404)

  loc = new_device['loc']
  query = {"loc": SON([("$near", loc), ("$maxDistance", 0.1)]), "name" : SON([("$ne", name)])}
  #query = {"loc": SON([("$near", loc)])}
  output = []
  for doc in device.find(query).limit(10):
    output.append({'name' : doc['name'], 'loc' : doc['loc'], "battery_level": doc['battery_level'], 
      "contributions": doc['contributions'], "nickname": doc['nickname']})
  return jsonify({'result' : output})
  
if __name__ == '__main__':
    app.run(port=8000, debug=True)