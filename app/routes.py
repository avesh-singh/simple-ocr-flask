from app import app
from flask import render_template, redirect, request, abort, url_for
from app.upload import UploadForm
import os
from werkzeug.utils import secure_filename
from app.utils import validate_image, read_fields
import requests


@app.route('/')
def index():
    form = UploadForm()
    return render_template('index.html', form=form)


@app.route('/', methods=['POST'])
def upload():
    uploaded = request.files['image']
    uploaded.stream.seek(0)
    filename = secure_filename(uploaded.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        # if file_ext not in app.config['UPLOAD_EXTENSIONS'] or file_ext != validate_image(uploaded.stream):
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            print(file_ext)
            print(validate_image(uploaded.stream))
            return "Invalid image", 400
        try:
            return read_fields(uploaded, file_ext)
        except AssertionError as e:
            return "not able to identify, {}".format(e), 400
    return redirect('/')
