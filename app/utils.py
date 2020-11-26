import imghdr
import requests
import base64
import io
from flask import send_file
from app import app
import re
from app.PANImage import PANImage

def read_fields(file, ext):
    pan_image = PANImage(file, ext)
    return pan_image.extract()
