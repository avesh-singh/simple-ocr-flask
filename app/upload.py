from flask_wtf import FlaskForm
from wtforms import SubmitField, TextField, DateField
from flask_wtf.file import FileField,FileRequired, FileAllowed


class DetailsForm(FlaskForm):
    name = TextField('Name')
    dob = DateField('Date of Birth')
    pan = TextField('Permanent Account Number')
