from flask import Blueprint, render_template, request
from app.models.announcement import Announcement
from app.models.blog import Blog

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Ana sayfa route'u"""
    # Son 5 duyuruyu getir
    announcements = Announcement.get_all(limit=5, active_only=True)
    
    # En çok görüntülenen 5 blog yazısını getir
    popular_blogs = Blog.get_all(limit=5, sort_by="views", sort_order=-1)
    
    return render_template('index.html', 
                           announcements=announcements,
                           popular_blogs=popular_blogs,
                           title="Ana Sayfa")

@main_bp.route('/about')
def about():
    """Hakkımızda sayfası"""
    return render_template('about.html', title="Hakkımızda")

@main_bp.route('/contact')
def contact():
    """İletişim sayfası"""
    return render_template('contact.html', title="İletişim")

@main_bp.route('/announcements')
def announcements():
    """Tüm duyuruları listele"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page
    
    # Duyuruları getir
    announcements_list = Announcement.get_all(limit=per_page, skip=skip, active_only=True)
    
    return render_template('announcements.html', 
                           announcements=announcements_list,
                           title="Duyurular",
                           page=page)

@main_bp.route('/announcement/<announcement_id>')
def announcement_detail(announcement_id):
    """Duyuru detayı sayfası"""
    announcement = Announcement.get_by_id(announcement_id)
    if not announcement or not announcement.is_active:
        return render_template('errors/404.html'), 404
    
    # Son 5 duyuruyu getir (mevcut duyuru hariç)
    recent_announcements = Announcement.get_all(limit=5, active_only=True)
    # Mevcut duyuruyu listeden çıkar
    recent_announcements = [a for a in recent_announcements if str(a._id) != announcement_id]
    
    return render_template('announcement_detail.html', 
                           announcement=announcement,
                           recent_announcements=recent_announcements,
                           title=announcement.title) 