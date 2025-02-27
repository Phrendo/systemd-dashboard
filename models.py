from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="unknown")
    last_heartbeat = db.Column(db.DateTime, nullable=True)
    last_checked = db.Column(db.DateTime, default=datetime.utcnow)
