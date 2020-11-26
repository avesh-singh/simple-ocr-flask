import re
import requests
from app import app
import json
import base64

class PANImage(object):
    
    def __init__(self, file, ext):
        file.stream.seek(0)
        self.b64image = base64.encodebytes(file.stream.read()).decode('utf-8')
        self.extracted, self.identified, self.has_overlay = self.identify(self.b64image, ext)
        self.overlay = self.extracted['TextOverlay']['Lines']
        self.name = ''
        self.dob = ''
        self.pan = ''
        self.name_box = ''
        self.dob_box = ''
        self.pan_box = ''
        self.name_words = ''
    
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
        # print(resp)
        # resp = static_resp
        identified = isinstance(resp, dict) and resp['OCRExitCode'] == 1 and not resp['IsErroredOnProcessing']
        assert identified, resp['ErrorMessage']
        extracted = resp['ParsedResults'][0]
        has_overlay = bool(extracted['TextOverlay']['HasOverlay'])
        return extracted, identified, has_overlay
    
    def check_(self):
        if not self.identified or not self.has_overlay:
            raise ValueError("No overlay found")
    
    def remove_unwanted_from_overlay(self):
        self.check_()
        it_dept = re.compile(r'INCOME TAX DEPARTMENT')
        pan_label = re.compile(r"Permanent Account Number( Card)?", flags=re.IGNORECASE)
        signature_label = re.compile(r'Signature', flags=re.IGNORECASE)
        govt_label = re.compile(r'GOVT\. OF INDIA', flags=re.IGNORECASE)
        name_label = re.compile(r"[^Father]+Name")
        father_label = re.compile(r"Father")
        clean_overlay = []
        for line in self.overlay:
            text = line['LineText']
            if not re.match(it_dept, text) and not re.match(pan_label, text) \
                and not re.search(signature_label, text) and not re.match(govt_label, text):
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
        print(list(map(lambda x: x['LineText'], clean_overlay)))
        return clean_overlay
    
    
    def extract_dob(self, list_overlay):
        self.check_()
        pattern = re.compile(r'\d{1,2}/\d{1,2}/\d{4}')
        index = -1
        for i, entity in enumerate(list_overlay):
            if re.fullmatch(pattern, entity['LineText']):
                self.dob = entity['LineText']
                self.dob_box = entity['Words']
                index = i
        return index
    
    
    def extract_pan(self, list_overlay):
        self.check_()
        pattern = re.compile(r'[A-Z0-9]{10}')
        index = -1
        for i, entity in enumerate(list_overlay):
            if re.fullmatch(pattern, entity['LineText']):
                self.pan = entity['LineText']
                self.pan_box = entity['Words']
                index = i
        return index
    
    
    
    def extract_name(self, list_overlay):
        self.check_()
        pattern = re.compile(r'[A-Z .]+')
        index = [-1, 0]
        for i, entity in enumerate(list_overlay):
            if re.fullmatch(pattern, entity['LineText']):
                if index[0] == -1:
                    index[0] = i
                    self.name = entity['LineText']
                    self.name_box = entity['Words']
                else:
                    index[1] = i
                    self.name += ' ' + entity['LineText']
                    self.name_box.extend(entity['Words'])
                    break
        return index
    
    def extract(self):
        clean_overlay = self.remove_unwanted_from_overlay()
        # clean_overlay = self.overlay
        ind = self.extract_dob(clean_overlay)
        # del clean_overlay[ind]
        ind = self.extract_pan(clean_overlay)
        # del clean_overlay[ind]
        ind = self.extract_name(clean_overlay)
        for i in range(ind[1], ind[0], -1):
            del clean_overlay[i]