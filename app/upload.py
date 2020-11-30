from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, DateField
from flask_wtf.file import FileField,FileRequired, FileAllowed


class DetailsForm(FlaskForm):
    name = StringField('Name')
    father = StringField("Father's Name")
    dob = DateField('Date of Birth')
    pan = StringField('Permanent Account Number')
