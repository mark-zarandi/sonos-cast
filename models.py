from datetime import datetime
from database import db
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class pod(db.Model):
    __tablename__ = 'pods'
    id = db.Column('pod_id', db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    address = db.Column(db.String)
    add_date = db.Column(db.DateTime)
    addresses = db.relationship('entry',backref='pod',lazy=True)

    def __init__(self, title, address):
        self.title = title
        self.address = address
        self.add_date = datetime.utcnow()

class entry(db.Model):
    __tablename__ = 'entries'
    id = db.Column('entry_id', db.Integer, primary_key=True)
    ep_num = db.Column(db.String(60))
    title = db.Column(db.String)
    l_date = db.Column(db.DateTime)
    pod_id = db.Column(db.Integer,db.ForeignKey(pod.id),nullable=False)
    def __init__(self, title, address):
        self.title = title
        self.address = address
        self.add_date = datetime.utcnow()

#also write entries class to capture previously listened pods