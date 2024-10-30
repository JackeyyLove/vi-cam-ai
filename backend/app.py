from flask import Flask, jsonify
from model import db
from config import Config
from model.conflict_report import ConflictReport
from model.map import Map
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()
    if not Map.query.first():
        sample_map = Map(name='Sample Map', image_url='image_url.jpg')
        db.session.add(sample_map)
    db.session.commit()
@app.route('/')
def home():
    return "Welcome to the Home Page!"

@app.route('/conflicts')
def get_conflicts():
    conflicts = ConflictReport.query.all()
    return jsonify([conflict.to_dict() for conflict in conflicts])

@app.route('/maps')
def get_maps():
    maps = Map.query.all()
    return jsonify([map.to_dict() for map in maps])
if __name__ == '__main__':
    app.run(debug=True)