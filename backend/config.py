# config.py
import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:mysql@localhost:3306/vicam'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
