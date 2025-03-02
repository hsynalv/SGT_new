from datetime import datetime
from bson import ObjectId
from app import mongo
from flask import current_app

class ActivityLog:
    """
    ActivityLog modeli - Kullanıcı etkinliklerini, hataları ve admin işlemlerini izlemek için kullanılır.
    """
    
    # Etkinlik türleri
    TYPE_USER = "user_action"  # Normal kullanıcı etkinliği
    TYPE_ADMIN = "admin_action"  # Admin etkinliği
    TYPE_ERROR = "error"  # Hata kaydı
    TYPE_SECURITY = "security"  # Güvenlikle ilgili olay
    
    # Alt kategoriler/eylemler
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_REGISTER = "register"
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_VIEW = "view"
    ACTION_SUBMIT = "submit"
    ACTION_DOWNLOAD = "download"
    ACTION_UPLOAD = "upload"
    
    def __init__(self, user_id=None, username=None, ip_address=None, type=TYPE_USER, 
                 action=None, description=None, module=None, entity_id=None, 
                 entity_type=None, details=None, timestamp=None):
        """
        ActivityLog constructor
        
        Args:
            user_id (str): Kullanıcı ID'si (yoksa None)
            username (str): Kullanıcı adı (yoksa None)
            ip_address (str): İstek IP adresi
            type (str): Etkinlik türü (user_action, admin_action, error, security)
            action (str): Gerçekleştirilen işlem (login, logout, create, update, delete, vb.)
            description (str): Etkinliğin kısa açıklaması
            module (str): İlgili modül/bölüm (auth, blog, courses, ctf, admin_panel, vb.)
            entity_id (str): Etkilenen nesnenin ID'si (varsa)
            entity_type (str): Etkilenen nesnenin türü (User, Blog, Challenge, vb.)
            details (dict): Ek detaylar ve bağlam bilgisi
            timestamp (datetime): Kaydın oluşturulma zamanı
        """
        self._id = ObjectId()
        self.user_id = user_id
        self.username = username
        self.ip_address = ip_address
        self.type = type
        self.action = action
        self.description = description
        self.module = module
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.details = details if details else {}
        self.timestamp = timestamp if timestamp else datetime.utcnow()
        
    def save(self):
        """Aktivite kaydını MongoDB'ye kaydet"""
        activity_dict = {
            "_id": self._id,
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "type": self.type,
            "action": self.action,
            "description": self.description,
            "module": self.module,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "details": self.details,
            "timestamp": self.timestamp
        }
        
        try:
            mongo.db.activity_logs.insert_one(activity_dict)
            current_app.logger.debug(f"Aktivite kaydedildi: {self.description}")
            return True
        except Exception as e:
            current_app.logger.error(f"Aktivite kaydı başarısız: {str(e)}")
            return False
        
    @staticmethod
    def get_all(limit=100, skip=0, type=None, user_id=None, module=None, 
                start_date=None, end_date=None, sort_by='timestamp', sort_order=-1):
        """
        Filtrelere göre etkinlik kayıtlarını getir
        
        Args:
            limit (int): Maksimum kayıt sayısı
            skip (int): Atlanacak kayıt sayısı (sayfalama için)
            type (str): Etkinlik türü filtresi
            user_id (str): Kullanıcı ID filtresi
            module (str): Modül filtresi
            start_date (datetime): Başlangıç tarihi filtresi
            end_date (datetime): Bitiş tarihi filtresi
            sort_by (str): Sıralama alanı
            sort_order (int): Sıralama yönü (1: artan, -1: azalan)
            
        Returns:
            list: ActivityLog nesnelerinin listesi
        """
        query = {}
        
        if type:
            query['type'] = type
        
        if user_id:
            query['user_id'] = user_id
            
        if module:
            query['module'] = module
            
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query['$gte'] = start_date
            if end_date:
                date_query['$lte'] = end_date
            if date_query:
                query['timestamp'] = date_query
                
        result = mongo.db.activity_logs.find(
            query
        ).sort(
            sort_by, sort_order
        ).skip(skip).limit(limit)
        
        logs = []
        for log_data in result:
            log = ActivityLog(
                user_id=log_data.get('user_id'),
                username=log_data.get('username'),
                ip_address=log_data.get('ip_address'),
                type=log_data.get('type'),
                action=log_data.get('action'),
                description=log_data.get('description'),
                module=log_data.get('module'),
                entity_id=log_data.get('entity_id'),
                entity_type=log_data.get('entity_type'),
                details=log_data.get('details'),
                timestamp=log_data.get('timestamp')
            )
            log._id = log_data.get('_id')
            logs.append(log)
            
        return logs
    
    @staticmethod
    def get_recent_user_activities(limit=10):
        """Son kullanıcı etkinliklerini getir"""
        return ActivityLog.get_all(limit=limit, type=ActivityLog.TYPE_USER)
    
    @staticmethod
    def get_recent_admin_activities(limit=10):
        """Son admin etkinliklerini getir"""
        return ActivityLog.get_all(limit=limit, type=ActivityLog.TYPE_ADMIN)
    
    @staticmethod
    def get_recent_errors(limit=10):
        """Son hata kayıtlarını getir"""
        return ActivityLog.get_all(limit=limit, type=ActivityLog.TYPE_ERROR)
    
    @staticmethod
    def get_user_activity_history(user_id, limit=50):
        """Belirli bir kullanıcının etkinlik geçmişini getir"""
        return ActivityLog.get_all(limit=limit, user_id=user_id)
    
    @staticmethod
    def get_count_by_type():
        """Etkinlik türlerine göre sayıları getir"""
        return mongo.db.activity_logs.aggregate([
            {"$group": {"_id": "$type", "count": {"$sum": 1}}}
        ])
    
    @staticmethod
    def delete_old_logs(days=30):
        """Belirli bir günden eski logları sil"""
        cutoff_date = datetime.utcnow() - datetime.timedelta(days=days)
        result = mongo.db.activity_logs.delete_many({"timestamp": {"$lt": cutoff_date}})
        return result.deleted_count 