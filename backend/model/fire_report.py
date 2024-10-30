from . import db 
class FireReport(db.Model):
    __tablename__ = 'fire_report'
    id = db.Column(db.Integer, primary_key=True)
    id_tracking = db.Column(db.Integer)
    real_time = db.Column(db.Integer)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'))
    image_url = db.Column(db.String(45))
    coordinate = db.Column(db.String(45))
    is_fire = db.Column(db.Integer)