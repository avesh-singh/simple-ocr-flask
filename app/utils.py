import imghdr
import requests
import base64
import io
from flask import send_file
from app import app
import re
from app.PANImage import PANImage

def validate_image(stream):
    header = stream.read(512)
    print(header)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')


def read_fields(file, ext):
    pan_image = PANImage(file, ext)
    pan_image.extract()
    # print(pan_image.name_box)
    # print(pan_image.dob_box)
    # print(pan_image.pan_box)
    # pattern = re.compile(r'\n((?:[A-Z .]+(?:\r\n)?)+)(\d+/\d+/\d+)\r\n[a-zPAN ]+\r\n([A-Z0-9]+)')
    # all_details = re.findall(pattern, parsed_text)
    # if len(all_details) > 0:
    #     all_details = all_details[0]
    # else:
    #     return {"error": "not able to identify!"}
    dob = pan_image.dob.split('/')
    dob_keys = ['day', 'month', 'year']
    dob_dict = dict(zip(dob_keys, dob))
    identified = {
        'name': {
                'text': pan_image.name,
                'box': pan_image.name_box,
            },
        'dob': {
                'text': dob_dict,
                'box': pan_image.dob_box
            },
        'pan': {
                'text': pan_image.pan,
                'box': pan_image.pan_box
        }
    }
    return identified
