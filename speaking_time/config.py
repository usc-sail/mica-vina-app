MAIL_SERVER = 'smtp.gmail.com'
MAIL_USERNAME = 'insert-gmail-account@gmail.com'
MAIL_PASSWORD = 'insert-gmail-passwd'
MAIL_USE_TLS =  True
MAIL_PORT = 587
ADMINS = ['rajatheb@usc.edu']
SECRET_KEY = 'dev'
MAIL_RECIPIENTS = ['']
MAIL_SUBJECT = 'Speaking Time Estimates for file ID '
SCRIPT_DIR = '/path/to/inference/scripts/'
OUT_DIR = '/path/to/output/dir'
UPLOAD_FOLDER = '/path/to/data/dir'
REDIS_URL = 'redis://localhost:6379'
QUEUES = ['default']
JOB_TIMEOUT=3600
SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite' #+
SQLALCHEMY_TRACK_MODIFICATIONS = False
