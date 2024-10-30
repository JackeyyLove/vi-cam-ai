from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .map import Map
from .camera import Camera
from .conflict_report import ConflictReport
from .fall_report import FallReport
from .fire_report import FireReport
from .person_report import PersonReport
# Import other models here as needed
