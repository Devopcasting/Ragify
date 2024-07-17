from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, StringField
from wtforms.validators import DataRequired

# Ask Query Form
class AskQueryForm(FlaskForm):
    query = StringField('Query', validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": "Ask question to your uploaded documents", "aria-describedby": "button-addon2"})
    answer = TextAreaField('Answer')
    submit = SubmitField('Submit')