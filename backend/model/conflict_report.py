from . import db 
class ConflictReport(db.Model):
    __tablename__ = 'conflict_report'
    id = db.Column(db.Integer, primary_key=True)
    id_tracking = db.Column(db.Integer)
    real_time = db.Column(db.Integer)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'))
    image_url = db.Column(db.String(45))
    
    def to_dict(self):
        return {
            'id': self.id,
            'id_tracking': self.id_tracking,
            'real_time': self.real_time,
            'camera_id': self.camera_id,
            'image_url': self.image_url
        }