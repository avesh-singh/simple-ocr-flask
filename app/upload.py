from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField,FileRequired, FileAllowed
# from wtforms.validators import 


class UploadForm(FlaskForm):
    image = FileField('Pan Card')
    submit = SubmitField('Upload')
