from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_admin import Admin

# MongoDB bağlantısı
mongo = PyMongo()

# Login yöneticisi
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bu sayfayı görüntülemek için giriş yapmalısınız.'
login_manager.login_message_category = 'info'

# Admin paneli
admin = Admin(name='Siber Topluluk', template_mode='bootstrap4')

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.get_by_id(user_id) 