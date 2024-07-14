from app import app, db

# Document Data model
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    path = db.Column(db.String(256), nullable=False)
    md5sum = db.Column(db.String(128), unique=True, nullable=False)
