from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app.models.announcement import Announcement
from app.models.blog import Blog
from app.models.user import User
from app.models import UserRole, Course, Lesson, Enrollment
from app.extensions import mongo
from bson.objectid import ObjectId
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from functools import wraps
from app.models.activity_log import ActivityLog
from app.utils.logger import log_user_activity
from app.utils.log_extension import log_activity

admin_bp = Blueprint('admin_panel', __name__, url_prefix='/admin')

def admin_required(f):
    """Admin yetkisi kontrolü için decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Dosya uzantısının izin verilip verilmediğini kontrol et"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin paneli ana sayfa route'u"""
    # Kullanıcı sayısı
    user_count = len(list(User.get_all()))
    
    # Blog yazısı sayısı
    blog_count = len(list(Blog.get_all()))
    
    # Duyuru sayısı
    announcement_count = len(list(Announcement.get_all(active_only=False)))
    
    # Kurs sayısı
    course_count = len(list(Course.get_all()))
    
    # CTF görevi sayısı
    ctf_challenge_count = mongo.db.ctf_challenges.count_documents({}) if 'ctf_challenges' in mongo.db.list_collection_names() else 0
    
    # Güncel zaman
    now = datetime.now()
    
    # Son kullanıcı aktivitelerini al
    try:
        # ActivityLog sınıfını kullanma
        # recent_activities = ActivityLog.get_recent_user_activities(limit=10)
        
        # Doğrudan MongoDB sorgusu kullan
        recent_activities = list(mongo.db.activity_logs.find({"type": "user_action"}).sort("timestamp", -1).limit(10))
    except Exception as e:
        print(f"Kullanıcı aktivite hatası: {str(e)}")
        recent_activities = []
    
    # Son admin aktivitelerini al
    try:
        # admin_activities = ActivityLog.get_recent_admin_activities(limit=5)
        
        # Doğrudan MongoDB sorgusu kullan
        admin_activities = list(mongo.db.activity_logs.find({"type": "admin_action"}).sort("timestamp", -1).limit(5))
    except Exception as e:
        print(f"Admin aktivite hatası: {str(e)}")
        admin_activities = []
    
    # Son hataları al
    try:
        # recent_errors = ActivityLog.get_recent_errors(limit=5)
        
        # Doğrudan MongoDB sorgusu kullan
        recent_errors = list(mongo.db.activity_logs.find({"type": "error"}).sort("timestamp", -1).limit(5))
    except Exception as e:
        print(f"Hata logları hatası: {str(e)}")
        recent_errors = []
    
    # Log sayılarını hesapla
    total_logs = mongo.db.activity_logs.count_documents({})
    
    # ActivityLog sabitleri yerine string değerler kullan
    user_logs = mongo.db.activity_logs.count_documents({"type": "user_action"})
    admin_logs = mongo.db.activity_logs.count_documents({"type": "admin_action"})
    error_logs = mongo.db.activity_logs.count_documents({"type": "error"})
    
    return render_template('admin/index.html',
                           title='Admin Paneli',
                           user_count=user_count,
                           blog_count=blog_count,
                           announcement_count=announcement_count,
                           course_count=course_count,
                           ctf_challenge_count=ctf_challenge_count,
                           now=now,
                           recent_activities=recent_activities,
                           admin_activities=admin_activities,
                           recent_errors=recent_errors,
                           total_logs=total_logs,
                           user_logs=user_logs,
                           admin_logs=admin_logs,
                           error_logs=error_logs)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Kullanıcı yönetimi route'u"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page
    
    users_cursor = mongo.db.users.find().skip(skip).limit(per_page)
    users_list = []
    
    for user_data in users_cursor:
        user = User.from_dict(user_data)
        users_list.append(user)
    
    total_users = mongo.db.users.count_documents({})
    total_pages = (total_users + per_page - 1) // per_page
    
    return render_template('admin/users.html', 
                           title='Kullanıcı Yönetimi',
                           users=users_list,
                           page=page,
                           total_pages=total_pages)

@admin_bp.route('/users/<user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Kullanıcı admin yetkisi değiştirme route'u"""
    user = User.get_by_id(user_id)
    if not user:
        abort(404)
    
    # Kendisini admin yetkisinden çıkarmasın
    if user_id == current_user.get_id():
        flash('Kendinizin admin yetkisini değiştiremezsiniz.', 'danger')
        return redirect(url_for('admin_panel.users'))
    
    # Admin yetkisini değiştir
    user.is_admin = not user.is_admin
    user.save()
    
    flash(f"'{user.username}' kullanıcısının admin yetkisi {'verildi' if user.is_admin else 'alındı'}.", 'success')
    return redirect(url_for('admin_panel.users'))

@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Kullanıcı silme route'u"""
    user = User.get_by_id(user_id)
    if not user:
        abort(404)
    
    # Kendisini silemesin
    if user_id == current_user.get_id():
        flash('Kendinizi silemezsiniz.', 'danger')
        return redirect(url_for('admin_panel.users'))
    
    # Kullanıcıyı sil
    username = user.username
    user_blogs = Blog.get_by_author(user_id)
    for blog in user_blogs:
        blog.delete()
    
    mongo.db.users.delete_one({"_id": ObjectId(user_id)})
    
    # Kullanıcıya ait kayıtları da temizle
    mongo.db.blogs.delete_many({'author_id': user_id})
    mongo.db.enrollments.delete_many({'user_id': user_id})
    
    flash(f"'{username}' kullanıcısı ve tüm blog yazıları silindi.", 'success')
    return redirect(url_for('admin_panel.users'))

@admin_bp.route('/blogs')
@login_required
@admin_required
def blogs():
    """Blog yazıları yönetimi route'u"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page
    
    blogs_cursor = mongo.db.blogs.find().sort('created_at', -1).skip(skip).limit(per_page)
    blogs_list = list(blogs_cursor)
    
    # Blog yazarlarının bilgilerini ekle
    for blog in blogs_list:
        author = mongo.db.users.find_one({"_id": ObjectId(blog.get('author_id', ''))})
        if author:
            blog['author'] = {
                'username': author.get('username', 'Bilinmeyen'),
                '_id': author.get('_id')
            }
    
    total_blogs = mongo.db.blogs.count_documents({})
    total_pages = (total_blogs + per_page - 1) // per_page
    
    return render_template('admin/blogs.html', 
                           title='Blog Yazıları Yönetimi',
                           blogs=blogs_list,
                           page=page,
                           total_pages=total_pages)

@admin_bp.route('/blogs/<blog_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_blog(blog_id):
    """Blog yazısı silme route'u"""
    blog = Blog.get_by_id(blog_id)
    if not blog:
        abort(404)
    
    # Blog yazısını sil
    title = blog.title
    blog.delete()
    
    flash(f"'{title}' başlıklı blog yazısı silindi.", 'success')
    return redirect(url_for('admin_panel.blogs'))

@admin_bp.route('/announcements')
@login_required
@admin_required
def announcements():
    """Duyurular yönetimi route'u"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page
    
    announcements_cursor = mongo.db.announcements.find().sort('created_at', -1).skip(skip).limit(per_page)
    announcements_list = list(announcements_cursor)
    
    total_announcements = mongo.db.announcements.count_documents({})
    total_pages = (total_announcements + per_page - 1) // per_page
    
    return render_template('admin/announcements.html', 
                           title='Duyurular Yönetimi',
                           announcements=announcements_list,
                           page=page,
                           total_pages=total_pages)

@admin_bp.route('/announcements/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_announcement():
    """Duyuru oluşturma route'u"""
    if request.method == 'POST':
        # Form verilerini al
        title = request.form.get('title')
        content = request.form.get('content')
        is_active = True if request.form.get('is_active') else False
        
        # Verileri doğrula
        error = None
        if not title:
            error = 'Başlık gerekli.'
        elif not content:
            error = 'İçerik gerekli.'
        
        # Hata yoksa duyuruyu oluştur
        if not error:
            # Resim varsa yükle
            image_url = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Benzersiz dosya adı oluştur
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    image_url = f"/static/uploads/{filename}"
            
            # Duyuruyu oluştur ve kaydet
            announcement = Announcement(
                title=title,
                content=content,
                author_id=current_user.get_id(),
                image_url=image_url,
                is_active=is_active
            )
            announcement.save()
            
            flash('Duyuru başarıyla oluşturuldu.', 'success')
            return redirect(url_for('admin_panel.announcements'))
        
        # Hata durumunda flash mesaj göster
        flash(error, 'danger')
    
    return render_template('admin/create_announcement.html', title='Duyuru Oluştur')

@admin_bp.route('/announcements/<announcement_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_announcement(announcement_id):
    """Duyuru düzenleme route'u"""
    announcement = Announcement.get_by_id(announcement_id)
    if not announcement:
        abort(404)
    
    if request.method == 'POST':
        # Form verilerini al
        title = request.form.get('title')
        content = request.form.get('content')
        is_active = True if request.form.get('is_active') else False
        
        # Verileri doğrula
        error = None
        if not title:
            error = 'Başlık gerekli.'
        elif not content:
            error = 'İçerik gerekli.'
        
        # Hata yoksa duyuruyu güncelle
        if not error:
            # Resim varsa yükle
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Benzersiz dosya adı oluştur
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    announcement.image_url = f"/static/uploads/{filename}"
            
            # Duyuruyu güncelle
            announcement.title = title
            announcement.content = content
            announcement.is_active = is_active
            announcement.save()
            
            flash('Duyuru başarıyla güncellendi.', 'success')
            return redirect(url_for('admin_panel.announcements'))
        
        # Hata durumunda flash mesaj göster
        flash(error, 'danger')
    
    return render_template('admin/edit_announcement.html', 
                           announcement=announcement, 
                           title='Duyuru Düzenle')

@admin_bp.route('/announcements/<announcement_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_announcement(announcement_id):
    """Duyuru silme route'u"""
    announcement = Announcement.get_by_id(announcement_id)
    if not announcement:
        abort(404)
    
    # Duyuruyu sil
    title = announcement.title
    announcement.delete()
    
    flash(f"'{title}' başlıklı duyuru silindi.", 'success')
    return redirect(url_for('admin_panel.announcements'))

@admin_bp.route('/announcements/<announcement_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_announcement(announcement_id):
    """Duyuru aktiflik durumunu değiştirme route'u"""
    announcement = Announcement.get_by_id(announcement_id)
    if not announcement:
        abort(404)
    
    # Duyuru durumunu değiştir
    announcement.is_active = not announcement.is_active
    announcement.save()
    
    flash(f"'{announcement.title}' başlıklı duyuru {'aktifleştirildi' if announcement.is_active else 'deaktif edildi'}.", 'success')
    return redirect(url_for('admin_panel.announcements'))

@admin_bp.route('/users/<user_id>/edit_role', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user_role(user_id):
    user = User.get_by_id(user_id)
    if not user:
        flash('Kullanıcı bulunamadı.', 'danger')
        return redirect(url_for('admin_panel.users'))
    
    if request.method == 'POST':
        new_role = request.form.get('role')
        
        # Rol doğrulama
        if new_role not in [UserRole.USER, UserRole.MEMBER, UserRole.ADMIN]:
            flash('Geçersiz rol seçimi.', 'danger')
            return redirect(url_for('admin_panel.edit_user_role', user_id=user_id))
        
        # Kullanıcının kendisini admin'den düşürmesini engelle
        if str(user._id) == current_user.get_id() and new_role != UserRole.ADMIN and user.role == UserRole.ADMIN:
            flash('Kendi admin yetkinizi kaldıramazsınız.', 'danger')
            return redirect(url_for('admin_panel.edit_user_role', user_id=user_id))
        
        user.role = new_role
        user.save()
        
        flash(f"Kullanıcı rolü başarıyla '{new_role}' olarak güncellendi.", 'success')
        return redirect(url_for('admin_panel.users'))
    
    return render_template('admin/edit_user_role.html', user=user, roles=UserRole)

@admin_bp.route('/courses')
@login_required
@admin_required
def courses():
    """Kurslar listesi route'u"""
    courses_list = Course.get_all()
    
    return render_template('admin/courses.html', courses=courses_list)

@admin_bp.route('/courses/<course_id>/enrollments')
@login_required
@admin_required
def course_enrollments(course_id):
    """Kurs kaydı olan kullanıcılar route'u"""
    course = Course.get_by_id(course_id)
    if not course:
        flash('Kurs bulunamadı.', 'danger')
        return redirect(url_for('admin_panel.courses'))
    
    enrollments = Enrollment.get_by_course(str(course._id))
    
    # Kayıt olan kullanıcıların bilgilerini getir
    enrolled_users = []
    for enrollment in enrollments:
        user = User.get_by_id(enrollment.user_id)
        if user:
            enrolled_users.append({
                'user': user,
                'enrollment': enrollment
            })
    
    return render_template('admin/course_enrollments.html', 
                          course=course, 
                          enrolled_users=enrolled_users)

@admin_bp.route('/logs')
@login_required
@admin_required
@log_activity('view', 'Admin log sayfasını görüntüledi', 'admin')
def logs():
    """Aktivite loglarını görüntüle"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    log_type = request.args.get('type', None)
    module = request.args.get('module', None)
    
    # Toplam log sayılarını hesapla
    total_logs = mongo.db.activity_logs.count_documents({})
    user_logs = mongo.db.activity_logs.count_documents({"type": "user_action"})
    admin_logs = mongo.db.activity_logs.count_documents({"type": "admin_action"})
    error_logs = mongo.db.activity_logs.count_documents({"type": "error"})
    security_logs = mongo.db.activity_logs.count_documents({"type": "security_action"})
    
    # Log tipine göre filtrele
    query = {}
    if log_type:
        query["type"] = log_type
    if module:
        query["module"] = module
    
    # Toplam kayıt sayısı
    total_filtered = mongo.db.activity_logs.count_documents(query)
    
    # Sayfalama
    skip = (page - 1) * per_page
    
    # ActivityLog.get_all yerine doğrudan MongoDB sorgusu kullan
    logs = list(mongo.db.activity_logs.find(query).sort("timestamp", -1).skip(skip).limit(per_page))
    
    # Benzersiz modülleri bul
    modules = mongo.db.activity_logs.distinct("module")
    
    # Sayfalama için toplam sayfa sayısını hesapla
    total_pages = (total_filtered + per_page - 1) // per_page
    
    return render_template(
        'admin/logs.html',
        logs=logs,
        total_logs=total_logs,
        user_logs=user_logs,
        admin_logs=admin_logs,
        error_logs=error_logs,
        security_logs=security_logs,
        modules=modules,
        active_type=log_type,
        active_module=module,
        page=page,
        total_pages=total_pages
    )

@admin_bp.route('/logs/<log_id>')
@login_required
@admin_required
def log_detail(log_id):
    """Log detayını görüntüle"""
    # ObjectId'ye dönüştür
    from bson import ObjectId
    log_data = mongo.db.activity_logs.find_one({"_id": ObjectId(log_id)})
    
    if not log_data:
        flash('Log kaydı bulunamadı', 'danger')
        return redirect(url_for('admin.logs'))
    
    return render_template('admin/log_detail.html', log=log_data) 