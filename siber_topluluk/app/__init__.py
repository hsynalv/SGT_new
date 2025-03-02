import os
from flask import Flask, render_template, send_from_directory
from app.config import get_config
from app.extensions import mongo, login_manager, admin
from flask_admin.contrib.pymongo import ModelView
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from flask_login import LoginManager
from flask import g
from datetime import datetime
from app.utils.log_extension import LoggingExtension

def create_app(test_config=None):
    """Flask uygulamasını oluştur ve yapılandır"""
    # Flask instance oluşturma
    app = Flask(__name__, instance_relative_config=True)
    
    # Konfigürasyonu yükle
    app.config.from_object(get_config())
    
    # MongoDB için URI'yi ayarla
    app.config['MONGO_URI'] = app.config.get('MONGODB_URI')
    
    # Test konfigürasyonu varsa onu uygula
    if test_config:
        app.config.update(test_config)
    
    # Uygulama klasörlerinin varlığından emin ol
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        pass
    
    # CTF dosyaları için klasörü oluştur
    try:
        os.makedirs(app.config['CTF_FILE_UPLOAD_PATH'], exist_ok=True)
    except OSError:
        pass
    
    # Eklentileri başlat
    mongo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Lütfen giriş yapın.'
    login_manager.login_message_category = 'info'
    admin.init_app(app)
    
    # Loglama uzantısını ayarla
    logging_ext = LoggingExtension(app)
    
    # Proxy ayarlarını uygula
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Admin paneline view'lar ekle
    from app.models.user import User
    from app.models.blog import Blog
    from app.models.announcement import Announcement
    
    # Korumalı blueprint'leri kaydet
    with app.app_context():
        # Auth route'larını kaydet
        from app.routes.auth_routes import auth_bp
        app.register_blueprint(auth_bp)
        
        # Blog route'larını kaydet
        from app.routes.blog_routes import blog_bp
        app.register_blueprint(blog_bp)
        
        # Admin route'larını kaydet
        from app.routes.admin_routes import admin_bp
        app.register_blueprint(admin_bp)
        
        # Ana sayfa route'unu kaydet
        from app.routes.main_routes import main_bp
        app.register_blueprint(main_bp)
        
        # Kurslar route'unu kaydet
        from app.routes.courses_routes import courses
        app.register_blueprint(courses, url_prefix='/courses')
        
        # CTF route'unu kaydet
        from app.routes.ctf_routes import ctf
        app.register_blueprint(ctf, url_prefix='/ctf')
        
        # Hata işleyicileri
        register_error_handlers(app)
    
    # Context processors
    @app.context_processor
    def utility_processor():
        return {'now': datetime.utcnow()}
    
    # Favicon için rota ekle
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')
    
    @app.route('/robots.txt')
    def robots():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'robots.txt', mimetype='text/plain')
    
    return app

def register_error_handlers(app):
    """Hata işleyicilerini kaydet"""
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500 