import re
import requests
from app import app
import json
import base64
from datetime import datetime


class PANImage(object):    
    def __init__(self, file, ext):
        file.stream.seek(0)
        self.b64image = base64.encodebytes(file.stream.read()).decode('utf-8')
        self.extracted, self.identified, self.has_overlay = self.identify(self.b64image, ext)
        self.overlay = self.extracted['TextOverlay']['Lines']
        self.name = None
        self.dob = None
        self.pan = None
        self.name_box = None
        self.dob_box = None
        self.pan_box = None
    
    
    def identify(self, image, ext):
        extracted = None
        has_overlay = False
        header = {'apikey': app.config['SECRET_KEY']}
        image = 'data:image/{};base64,'.format(ext[1:]) + image
        data = {
            "language": "eng",
            "isOverlayRequired":"true",
            "base64Image": image,
            "iscreatesearchablepdf": "false",
            "issearchablepdfhidetextlayer": "false",
            "filetype": ext,
        }
        resp = requests.post(app.config['API_ENDPOINT'], data=data, headers=header)
        resp = json.loads(resp.text)
        identified = isinstance(resp, dict) and resp['OCRExitCode'] == 1 and not resp['IsErroredOnProcessing']
        assert identified, resp['ErrorMessage']
        extracted = resp['ParsedResults'][0]
        has_overlay = bool(extracted['TextOverlay']['HasOverlay'])
        return extracted, identified, has_overlay
    
    
    def check_(self):
        if not self.identified or not self.has_overlay:
            raise ValueError("No overlay found")
    
    
    def remove_unwanted_from_overlay(self):
        '''
        this methods cleans the overlay field of unwanted text that may have been recognized
        by third-party API
        '''
        self.check_()
        
        it_dept = re.compile(r'INCOME\s?TAX\s?DEPARTMENT')
        pan_label = re.compile(r"Permanent Account Number( Card)?", flags=re.IGNORECASE)
        signature_label = re.compile(r'Signature', flags=re.IGNORECASE)
        govt_label = re.compile(r'GOVT(\.)?\s?OF\s?INDIA', flags=re.IGNORECASE)
        
        # newer PAN cards have Father's Name also
        name_label = re.compile(r"[^Father]+Name")
        father_label = re.compile(r"Father")
        
        clean_overlay = []
        for line in self.overlay:
            text = line['LineText']
            if not re.search(it_dept, text) and not re.match(pan_label, text) \
                and not re.search(signature_label, text) and not re.search(govt_label, text):
                clean_overlay.append(line)
        i = 0
        while i < len(clean_overlay):
            text = clean_overlay[i]['LineText'] 
            if re.search(father_label, text):
                del clean_overlay[i]
                del clean_overlay[i]
            elif re.search(name_label, text):
                del clean_overlay[i]
            else:
                i += 1
        return clean_overlay
    
    
    def extract_fields(self, list_overlay):
        self.check_()
        
        dob_pattern = re.compile(r'([0-9 ]+)/([0-9 ]+)/([0-9 ]+)')
        pan_pattern = re.compile(r'[A-Z0-9]{10}')
        name_pattern = re.compile(r'[A-Z .]+')
        
        name_found = False
        for i, entity in enumerate(list_overlay):
            text = entity['LineText']
            
            if re.fullmatch(dob_pattern, text):
                self.dob = text.replace(' ','')
                self.dob_box = entity['Words']
            
            elif re.fullmatch(pan_pattern, text):
                self.pan = text
                self.pan_box = entity['Words']
            
            elif re.fullmatch(name_pattern, text):
                
                if not name_found:
                    name_found = True
                    self.name = text
                    self.name_box = entity['Words']
                else:
                    self.name += ' ' + text
                    self.name_box.extend(entity['Words'])

    
    def extract(self):
        clean_overlay = self.remove_unwanted_from_overlay()
        print(clean_overlay)
        self.extract_fields(clean_overlay)
        dob = self.dob.split('/')
        dob_keys = ['day', 'month', 'year']
        dob_dict = dict(zip(dob_keys, dob))
        identified = {
            'name': {
                    'text': self.name,
                    'box': self.name_box,
                },
            'dob': {
                    'text': datetime.strptime(self.dob, '%d/%m/%Y'),
                    'parts':dob_dict,
                    'box': self.dob_box
                },
            'pan': {
                    'text': self.pan,
                    'box': self.pan_box
            }
        }
        return identified
