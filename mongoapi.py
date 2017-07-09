from flask import Flask
from flask import jsonify
from flask import request
from flask_pymongo import PyMongo
from pymongo import GEO2D

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

if __name__ == '__main__':
    app.run(debug=True)