from flask import Flask
from flask import jsonify
from flask import request
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
      "contributions": s['contributions']})
  return jsonify({'result' : output})

@app.route('/device/<name>', methods=['GET'])
def get_one_device(name):
  device = mongo.db.devices
  s = device.find_one({'name' : name})
  if s:
    output = {'name' : s['name'], 'loc' : s['loc'], "battery_level": s['battery_level'], 
      "contributions": s['contributions']}
  else:
    output = "No such name"
  return jsonify({'result' : output})

@app.route('/register', methods=['POST'])
def add_device():
  #mongo.db.devices.create_index([("loc", GEO2D)])
  device = mongo.db.devices
  name = request.json['name']
  loc = request.json['loc']
  s = device.find_one({'name' : name})
  if s:
    output = "device already registered"
  else:
    battery_level = request.json['battery_level']
    device_id = device.insert({'name': name, 'battery_level': battery_level, 
      'loc' : loc, "contributions": 1 })
    new_device = device.find_one({'_id': device_id })
    output = {'name' : new_device['name'], 'loc' : new_device['loc'], "battery_level": new_device['battery_level'], 
        "contributions": new_device['contributions']}
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
        "contributions": new_device['contributions']}
    return jsonify({'result' : output})
  else:
    abort(404)

@app.route('/nearby/<name>/<lon>/<lat>', methods=['GET'])
def get_nearby_devices(name, lon, lat):
  device = mongo.db.devices
  loc = [lon, lat]
  query = {"loc": SON([("$near", loc), ("$maxDistance", 5)])}
  output = []
  for doc in device.find(query).limit(10):
    output.append({'name' : doc['name'], 'loc' : doc['loc'], "battery_level": doc['battery_level'], 
      "contributions": doc['contributions']})
  return jsonify({'result' : output})
  
if __name__ == '__main__':
    app.run(debug=True)