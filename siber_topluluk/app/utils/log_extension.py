from flask import request, g, current_app
from app.utils.logger import log_error, log_user_activity
from functools import wraps
import time

class LoggingExtension:
    """
    Flask uygulamasına entegre edilebilen loglama uzantısı.
    
    Özellikler:
    - Tüm istekleri loglama
    - Hataları otomatik yakalama ve loglama
    - Performans izleme
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Flask uygulamasını yapılandır"""
        # Hata işleyicileri ekle
        app.register_error_handler(Exception, self._handle_error)
        
        # İstek öncesi ve sonrası kancaları ekle
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
    def _before_request(self):
        """Her istek öncesi çalışır - zaman damgası ekler"""
        g.start_time = time.time()
    
    def _after_request(self, response):
        """İstek tamamlandığında çalışan metot"""
        # Başlangıç zamanını al
        start_time = getattr(g, 'start_time', None)
        if start_time:
            # İstek süresini hesapla
            duration = time.time() - start_time
            path = request.path

            # Sadece başarılı istekleri logla (200-299 arası)
            if 200 <= response.status_code < 300:
                # İstek metodunu al
                method = request.method
                # Kullanıcı ajanını al
                user_agent = request.headers.get('User-Agent', None)
                
                # View aksiyon mu yoksa form submit mi olduğunu belirle
                action = 'submit' if method in ['POST', 'PUT', 'DELETE', 'PATCH'] else 'view'
                
                # Sadece önemli view aksiyonları logla
                if action == 'view' and not self._should_log_view(path):
                    return response

                # Log açıklamasını oluştur
                description = f"{method} {path}"
                
                # Ayrıntıları hazırla
                details = {
                    'method': method,
                    'path': path,
                    'status_code': response.status_code,
                    'execution_time': f"{duration:.4f}s",
                    'user_agent': user_agent
                }

                # Kullanıcı aktivitesini logla
                module = path.split('/')[1] if len(path.split('/')) > 1 else 'main'
                log_user_activity(action, description, module, details=details)

            # Performans metriğini header'a ekle
            response.headers['X-Response-Time'] = f"{duration:.4f}s"
        
        return response
    
    def _handle_error(self, e):
        """Hataları yakala ve logla"""
        # Modülü belirle
        module = 'unknown'
        if request.endpoint:
            module_parts = request.endpoint.split('.')
            if len(module_parts) > 0:
                module = module_parts[0]
        
        # Hata detayları
        details = {
            'url': request.url,
            'method': request.method,
            'headers': dict(request.headers),
        }
        
        # Hatayı logla
        log_error(e, module, details=details)
        
        # Hata işleyicisinin çalışmasına izin ver
        return current_app.handle_exception(e)

    def _should_log_view(self, path):
        """
        Görüntüleme işleminin loglanıp loglanmaması gerektiğini belirle
        Önemli sayfalar için True, sıradan sayfalar için False döndür
        """
        # Önemli sayfa yolları - bunlar her zaman loglanmalı
        important_paths = [
            '/admin', 
            '/profile', 
            '/ctf/challenges',
            '/auth/login',
            '/auth/register',
            '/courses/enroll'
        ]
        
        # Path'in önemli yollardan biriyle başlayıp başlamadığını kontrol et
        for important_path in important_paths:
            if path.startswith(important_path):
                return True
        
        return False

def log_activity(action, description, module, entity_id=None, entity_type=None):
    """
    Decorator: Bir fonksiyonun çalışmasını loglamak için
    
    Örnek kullanım:
    @log_activity('create', 'Yeni blog yazısı oluşturuldu', 'blog')
    def create_blog():
        # ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Fonksiyonu çalıştır
                result = f(*args, **kwargs)
                
                # Başarılı ise logla
                details = {'args': args, 'kwargs': {k: v for k, v in kwargs.items() if k != 'password'}}
                log_user_activity(action, description, module, 
                                 entity_id=entity_id, entity_type=entity_type,
                                 details=details)
                return result
                
            except Exception as e:
                # Hatayı logla
                log_error(e, module, description=f"Error in {f.__name__}: {str(e)}")
                raise  # Hatayı yeniden yükselt
                
        return decorated_function
    return decorator 