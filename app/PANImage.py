import re
import requests
from app import app
import json
import base64
from datetime import datetime


class PANImage(object):
    def __init__(self, file, ext):
        file.stream.seek(0)
        img_bytes = base64.encodebytes(file.stream.read())
        self.b64image = img_bytes.decode('utf-8')
        self.extracted, self.identified, self.has_overlay = self.identify(self.b64image, ext)
        self.overlay = self.extracted['TextOverlay']['Lines']
        simple_details = {
            'text': '',
            'box': None,
            'min_top': -1,
        }
        self.response = {
            'name': simple_details.copy(),
            'dob': simple_details.copy(),
            'pan': simple_details.copy(),
            'father': simple_details.copy()
        }

    def identify(self, image, ext):
        header = {'apikey': app.config['SECRET_KEY']}
        image = 'data:image/{};base64,'.format(ext[1:]) + image
        data = {
            "language": "eng",
            "isOverlayRequired": "true",
            "base64Image": image,
            "iscreatesearchablepdf": "false",
            "issearchablepdfhidetextlayer": "false",
            "filetype": ext,
            "OCREngine": 2
        }
        resp = requests.post(app.config['API_ENDPOINT'], data=data, headers=header)
        resp = json.loads(resp.text)
        # resp = sample_resp
        identified = isinstance(resp, dict) and resp['OCRExitCode'] == 1 and not resp['IsErroredOnProcessing']
        assert identified, resp['ErrorMessage']
        extracted = resp['ParsedResults'][0]
        has_overlay = bool(extracted['TextOverlay']['HasOverlay'])
        return extracted, identified, has_overlay

    def extract_fields(self):
        assert self.identified and self.has_overlay, "No overlay found"
        dob_pattern = re.compile(r'([0-9 ]+)/([0-9 ]+)/([0-9 ]+)')
        pan_pattern = re.compile(r'[A-Z0-9]{10}')
        name_pattern = re.compile(r'[A-Z1045 .]+')
        it_dept = re.compile(r'(INCOME|TAX|DEPARTMENT)')
        pan_label = re.compile(r"(Permanent|Account|Number|Card)", flags=re.IGNORECASE)
        signature_label = re.compile(r'Sign(ature)?', flags=re.IGNORECASE)
        govt_label = re.compile(r'(GOVT(\.)?|OF|INDIA)', flags=re.IGNORECASE)

        clean_overlay = []
        for line in self.overlay:
            text = line['LineText']
            if not re.search(it_dept, text) and not re.search(pan_label, text) \
                    and not re.search(signature_label, text) and not re.search(govt_label, text):
                clean_overlay.append(line)
        name_candidates = []
        record_bounds = [float('inf'), 0]
        max_width = 1
        for i, entity in enumerate(clean_overlay):
            text = entity['LineText']
            left = entity['Words'][0]['Left']
            if record_bounds[0] > left:
                record_bounds[0] = left
                max_width = record_bounds[1] - record_bounds[0]
            elif record_bounds[1] < entity['Words'][-1]['Left'] + entity['Words'][-1]['Width']:
                record_bounds[1] = entity['Words'][-1]['Left'] + entity['Words'][-1]['Width']
                max_width = record_bounds[1] - record_bounds[0]

            if re.fullmatch(dob_pattern, text):
                self.response['dob']['text'] = text.replace(' ', '')
                self.response['dob']['box'] = entity['Words']
                self.response['dob']['min_top'] = entity['MinTop']
            elif re.fullmatch(pan_pattern, text):
                self.response['pan']['text'] = text
                self.response['pan']['box'] = entity['Words']
                self.response['pan']['min_top'] = entity['MinTop']
            # if current text matches name pattern, save it for later
            elif re.fullmatch(name_pattern, text):
                name_candidates.append(entity)

        for i, entity in enumerate(name_candidates):
            if abs(entity['Words'][0]['Left'] - self.response['dob']['box'][0]['Left']) / max_width < 0.05:
                if self.response['name']['min_top'] < 0:
                    self.response['name']['text'] = entity['LineText']
                    self.response['name']['box'] = entity['Words']
                    self.response['name']['min_top'] = entity['MinTop']
                elif self.response['father']['min_top'] < 0 < self.response['name']['min_top']:
                    if entity['MinTop'] < self.response['name']['min_top']:
                        continue
                    self.response['father']['text'] = entity['LineText']
                    self.response['father']['box'] = entity['Words']
                    self.response['father']['min_top'] = entity['MinTop']

    def extract(self):
        self.extract_fields()
        dob_text = self.response['dob']['text']
        dob = dob_text.split('/')
        self.response['dob']['text'] = datetime.strptime(dob_text, '%d/%m/%Y')
        dob_keys = ['day', 'month', 'year']
        self.response['dob']['parts'] = dict(zip(dob_keys, dob))
        return self.response
