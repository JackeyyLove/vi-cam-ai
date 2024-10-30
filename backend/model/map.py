# models/map.py
from . import db

class Map(db.Model):
    __tablename__ = 'map'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'image_url': self.image_url
        }