import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

class Config:
    """Temel konfigürasyon sınıfı"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'zorlanacakbirgizlianahtar'
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/sgt'
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1', 't']
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024  # 64 MB max upload
    
    # CTF platform ayarları
    CTF_FILE_UPLOAD_PATH = os.path.join(UPLOAD_FOLDER, 'ctf_files')
    CTF_FLAG_PREFIX = 'CTF{'
    CTF_FLAG_SUFFIX = '}'
    
    # Mail ayarları
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Oturum ayarları
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 saat

class DevelopmentConfig(Config):
    """Geliştirme ortamı konfigürasyonu"""
    DEBUG = True

class ProductionConfig(Config):
    """Üretim ortamı konfigürasyonu"""
    DEBUG = False

class TestingConfig(Config):
    """Test ortamı konfigürasyonu"""
    TESTING = True
    MONGODB_URI = 'mongodb://localhost:27017/siber_topluluk_test'

# Çalışma ortamına göre konfigürasyonu seç
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Çevre değişkenine göre uygun konfigürasyonu döndür"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default']) 