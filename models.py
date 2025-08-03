# models.py
from datetime import datetime
from extensions import db

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(150))
    password = db.Column(db.String(200))

class PasswordResetRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(150), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
