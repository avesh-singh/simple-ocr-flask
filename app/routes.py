from app import app
from flask import render_template, redirect, request, flash, url_for
from app.upload import DetailsForm
import os
from werkzeug.utils import secure_filename
from app.utils import read_fields
import requests


@app.route('/', methods=['GET', 'POST'])
def upload():
    form = DetailsForm()
    if request.method == 'POST':    
        uploaded = request.files['image']
        uploaded.stream.seek(0)
        filename = secure_filename(uploaded.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                return "Invalid image", 400
            try:
                fields = read_fields(uploaded, file_ext)
                flash("PAN is successfully uploaded and form is pre-filled for you!")
                form.dob.data = fields['dob']['text']
                form.pan.data = fields['pan']['text']
                form.name.data = fields['name']['text']
                form.father.data = fields['father']['text']
                return render_template('index.html', form=form)
            except AssertionError as e:
                return "not able to identify, {}".format(e), 400
    return render_template('index.html', form=form)
