from flask import request, current_app, g, has_request_context
from flask_login import current_user
from app.models.activity_log import ActivityLog
import traceback

def log_user_activity(action, description, module, entity_id=None, entity_type=None, details=None):
    """
    Kullanıcı etkinliğini logla
    
    Args:
        action (str): Gerçekleştirilen işlem (login, logout, create, update, delete, vb.)
        description (str): Etkinliğin kısa açıklaması
        module (str): İlgili modül/bölüm (auth, blog, courses, ctf, admin_panel, vb.)
        entity_id (str): Etkilenen nesnenin ID'si (varsa)
        entity_type (str): Etkilenen nesnenin türü (User, Blog, Challenge, vb.)
        details (dict): Ek detaylar
    """
    # Kullanıcı bilgilerini al
    user_id = None
    username = None
    
    if has_request_context():
        # Eğer kullanıcı oturum açmışsa kullanıcı bilgilerini ekle
        if current_user and current_user.is_authenticated:
            user_id = current_user.get_id()
            username = current_user.username
        
        # IP adresini al
        ip_address = request.remote_addr
    else:
        ip_address = None
    
    # Admin kullanıcısı kontrolü
    is_admin_user = _is_admin_user()
    
    # Log tipini belirle
    log_type = ActivityLog.TYPE_ADMIN if is_admin_user else ActivityLog.TYPE_USER
    
    # Log oluştur ve kaydet
    log = ActivityLog(
        user_id=user_id,
        username=username,
        ip_address=ip_address,
        type=log_type,
        action=action,
        description=description,
        module=module,
        entity_id=entity_id,
        entity_type=entity_type,
        details=details
    )
    log.save()
    
    return log

def log_error(error, module, description=None, details=None):
    """
    Hata kaydet
    
    Args:
        error (Exception): Hata nesnesi
        module (str): Hatanın oluştuğu modül
        description (str): Hatanın kısa açıklaması (varsayılan: hata mesajı)
        details (dict): Ek detaylar
    """
    ip_address = request.remote_addr if request else None
    user_id = None
    username = None
    
    if hasattr(g, 'user') and g.user:
        user_id = str(g.user._id) if hasattr(g.user, '_id') else None
        username = g.user.username if hasattr(g.user, 'username') else None
    
    if not description:
        description = str(error)
    
    error_details = {
        'error_type': error.__class__.__name__,
        'traceback': traceback.format_exc()
    }
    
    if details:
        error_details.update(details)
    
    activity = ActivityLog(
        user_id=user_id,
        username=username,
        ip_address=ip_address,
        type=ActivityLog.TYPE_ERROR,
        action='error',
        description=description,
        module=module,
        details=error_details
    )
    
    return activity.save()

def log_security_event(action, description, module, details=None):
    """
    Güvenlik olayını logla (başarısız giriş denemeleri, şüpheli etkinlikler, vb.)
    
    Args:
        action (str): Olay türü
        description (str): Olayın kısa açıklaması
        module (str): İlgili modül
        details (dict): Ek detaylar
    """
    ip_address = request.remote_addr
    user_id = None
    username = None
    
    if hasattr(g, 'user') and g.user:
        user_id = str(g.user._id) if hasattr(g.user, '_id') else None
        username = g.user.username if hasattr(g.user, 'username') else None
    
    activity = ActivityLog(
        user_id=user_id,
        username=username,
        ip_address=ip_address,
        type=ActivityLog.TYPE_SECURITY,
        action=action,
        description=description,
        module=module,
        details=details
    )
    
    # Güvenlik olaylarını console'a da yazdır
    current_app.logger.warning(f"Security Event: {description} | IP: {ip_address} | User: {username}")
    
    return activity.save()

def _is_admin_user():
    """Kullanıcının admin olup olmadığını kontrol et"""
    if has_request_context() and current_user and current_user.is_authenticated:
        return current_user.is_admin
    return False 