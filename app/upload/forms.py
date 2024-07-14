from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField
from wtforms.validators import DataRequired
import os

# Upload form class
class UploadForm(FlaskForm):
    file = FileField('Upload Documents',validators=[DataRequired()])
    submit = SubmitField('Upload')