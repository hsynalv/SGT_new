import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Flask uygulaması için temel konfigürasyon sınıfı"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gizli-anahtar-buraya'
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/siber_topluluk'
    DEBUG = True
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max yükleme boyutu
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'zip', 'txt', 'md'}
    
    # CTF platform ayarları
    CTF_FILE_UPLOAD_PATH = os.path.join(UPLOAD_FOLDER, 'ctf_files')
    CTF_FLAG_PREFIX = 'CTF{'
    CTF_FLAG_SUFFIX = '}'

class DevelopmentConfig(Config):
    """Geliştirme ortamı konfigürasyonu"""
    DEBUG = True

class TestingConfig(Config):
    """Test ortamı konfigürasyonu"""
    TESTING = True
    MONGODB_URI = os.environ.get('TEST_MONGODB_URI') or 'mongodb://localhost:27017/siber_topluluk_test'

class ProductionConfig(Config):
    """Canlı ortam konfigürasyonu"""
    DEBUG = False
    TESTING = False

# Konfigürasyon sözlüğü
config_dict = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Uygun konfigürasyon sınıfını döndürür"""
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config_dict.get(config_name, config_dict['default']) 