from . import db
class FallReport(db.Model):
    __tablename__ = 'fall_report'
    id = db.Column(db.Integer, primary_key=True)
    id_tracking = db.Column(db.Integer)
    real_time = db.Column(db.Integer)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'))
    image_url = db.Column(db.String(45))
    coordinates = db.Column(db.String(45))
    percent = db.Column(db.Integer)