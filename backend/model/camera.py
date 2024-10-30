from . import db 
class Camera(db.Model):
    __tablename__ = 'cameras'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rtsp = db.Column(db.String(100))
    status = db.Column(db.Integer)
    time_start = db.Column(db.DateTime)
    vehicle_analyze = db.Column(db.Integer)
    human_analyze = db.Column(db.Integer)
    fire_analyze = db.Column(db.Integer)
    fall_analyze = db.Column(db.Integer)
    polygon_warning = db.Column(db.Text)
    coordinate_map = db.Column(db.String(45))
