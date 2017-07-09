from flask import Flask
from flask import jsonify
from flask import request
from flask_pymongo import PyMongo

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'mycrowdcharger'
app.config['MONGO_URI'] = 'mongodb://spyros.hopto.org:27017/mycrowdcharger'

mongo = PyMongo(app)

@app.route('/device', methods=['GET'])
def get_all_devices():
  device = mongo.db.devices
  output = []
  for s in device.find():
    output.append({'name' : s['name'], 'loc' : s['loc'], "battery_level": s['battery_level']})
  return jsonify({'result' : output})

@app.route('/star/', methods=['GET'])
def get_one_star(name):
  star = mongo.db.stars
  s = star.find_one({'name' : name})
  if s:
    output = {'name' : s['name'], 'distance' : s['distance']}
  else:
    output = "No such name"
  return jsonify({'result' : output})

@app.route('/star', methods=['POST'])
def add_star():
  star = mongo.db.stars
  name = request.json['name']
  distance = request.json['distance']
  star_id = star.insert({'name': name, 'distance': distance})
  new_star = star.find_one({'_id': star_id })
  output = {'name' : new_star['name'], 'distance' : new_star['distance']}
  return jsonify({'result' : output})

if __name__ == '__main__':
    app.run(debug=True)