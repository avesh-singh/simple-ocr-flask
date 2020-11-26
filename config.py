import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# figure out a way to securely configure api key
class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or 'helloworld'
    MAX_CONTENT_LENGTH=1024 * 1024
    UPLOAD_EXTENSIONS = ['.jpg', '.png', '.jpeg']
    UPLOAD_PATH = 'uploads'
    API_ENDPOINT = 'https://api.ocr.space/parse/image'