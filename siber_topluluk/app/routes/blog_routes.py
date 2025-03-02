from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.models.blog import Blog
from bson.objectid import ObjectId
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import markdown
import bleach

blog_bp = Blueprint('blog', __name__, url_prefix='/blog')

def allowed_file(filename):
    """Dosya uzantısının izin verilip verilmediğini kontrol et"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def md_to_html(text):
    """Markdown metnini güvenli HTML'e dönüştürür veya zaten HTML ise temizler"""
    # Eğer içerik zaten HTML gibi görünüyorsa (TinyMCE kullanıldığında)
    if text.strip().startswith('<') and ('</p>' in text or '</div>' in text or '</h' in text):
        # Bu zaten HTML, sadece temizle
        allowed_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'a', 'ul', 'ol', 'li', 
                    'strong', 'em', 'code', 'pre', 'blockquote', 'img', 'span', 'div', 'table', 
                    'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'b', 'i', 'u', 'strike', 'sub', 'sup']
        allowed_attrs = {
            '*': ['class', 'style', 'id'],
            'a': ['href', 'title', 'target', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height', 'style'],
            'table': ['border', 'cellpadding', 'cellspacing', 'width'],
        }
        return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs)
    else:
        # Markdown olarak işle
        allowed_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'a', 'ul', 'ol', 'li', 
                    'strong', 'em', 'code', 'pre', 'blockquote', 'img', 'span', 'div', 'table', 
                    'thead', 'tbody', 'tr', 'th', 'td', 'hr']
        allowed_attrs = {
            '*': ['class', 'style'],
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
        }
        html = markdown.markdown(text, extensions=['extra', 'codehilite', 'tables'])
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)

@blog_bp.route('/')
def index():
    """Blog listesi route'u"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page
    
    # Blog yazılarını getir
    blogs = Blog.get_all(limit=per_page, skip=skip)
    
    return render_template('blog/index.html', 
                           blogs=blogs, 
                           title="Blog",
                           page=page)

@blog_bp.route('/<blog_id>')
def detail(blog_id):
    """Blog detay sayfası route'u"""
    blog = Blog.get_by_id(blog_id)
    if not blog:
        abort(404)
    
    # Markdown içeriğini HTML'e dönüştür
    blog.content_html = md_to_html(blog.content)
    
    # Görüntülenme sayısını arttır
    blog.increment_views()
    
    return render_template('blog/detail.html', blog=blog, title=blog.title)

@blog_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Blog yazısı oluşturma route'u"""
    if request.method == 'POST':
        # Form verilerini al
        title = request.form.get('title')
        content = request.form.get('content')
        tags = request.form.get('tags', '').split(',')
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        # Verileri doğrula
        error = None
        if not title:
            error = 'Başlık gerekli.'
        elif not content:
            error = 'İçerik gerekli.'
        
        # Hata yoksa blog yazısını oluştur
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
            
            # Blog yazısını oluştur ve kaydet
            blog = Blog(
                title=title,
                content=content,
                author_id=current_user.get_id(),
                tags=tags,
                image_url=image_url
            )
            blog.save()
            
            flash('Blog yazısı başarıyla oluşturuldu.', 'success')
            return redirect(url_for('blog.detail', blog_id=blog._id))
        
        # Hata durumunda flash mesaj göster
        flash(error, 'danger')
    
    return render_template('blog/create.html', title='Blog Yazısı Oluştur')

@blog_bp.route('/<blog_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(blog_id):
    """Blog yazısı düzenleme route'u"""
    blog = Blog.get_by_id(blog_id)
    if not blog:
        abort(404)
    
    # Kullanıcı yetki kontrolü
    if str(blog.author_id) != current_user.get_id() and not current_user.is_admin:
        flash('Bu blog yazısını düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('blog.detail', blog_id=blog_id))
    
    if request.method == 'POST':
        # Form verilerini al
        title = request.form.get('title')
        content = request.form.get('content')
        tags = request.form.get('tags', '').split(',')
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        # Verileri doğrula
        error = None
        if not title:
            error = 'Başlık gerekli.'
        elif not content:
            error = 'İçerik gerekli.'
        
        # Hata yoksa blog yazısını güncelle
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
                    blog.image_url = f"/static/uploads/{filename}"
            
            # Blog yazısını güncelle
            blog.title = title
            blog.content = content
            blog.tags = tags
            blog.save()
            
            flash('Blog yazısı başarıyla güncellendi.', 'success')
            return redirect(url_for('blog.detail', blog_id=blog._id))
        
        # Hata durumunda flash mesaj göster
        flash(error, 'danger')
    
    return render_template('blog/edit.html', blog=blog, title='Blog Yazısını Düzenle')

@blog_bp.route('/<blog_id>/delete', methods=['POST'])
@login_required
def delete(blog_id):
    """Blog yazısı silme route'u"""
    blog = Blog.get_by_id(blog_id)
    if not blog:
        abort(404)
    
    # Kullanıcı yetki kontrolü
    if str(blog.author_id) != current_user.get_id() and not current_user.is_admin:
        flash('Bu blog yazısını silme yetkiniz yok.', 'danger')
        return redirect(url_for('blog.detail', blog_id=blog_id))
    
    # Blog yazısını sil
    blog.delete()
    
    flash('Blog yazısı başarıyla silindi.', 'success')
    return redirect(url_for('blog.index'))

@blog_bp.route('/<blog_id>/like', methods=['POST'])
@login_required
def like(blog_id):
    """Blog yazısı beğenme route'u"""
    blog = Blog.get_by_id(blog_id)
    if not blog:
        abort(404)
    
    # Blog yazısını beğen
    user_id = current_user.get_id()
    if user_id in blog.likes:
        blog.remove_like(user_id)
        message = 'Beğeni kaldırıldı.'
    else:
        blog.add_like(user_id)
        message = 'Blog yazısı beğenildi.'
    
    flash(message, 'success')
    return redirect(url_for('blog.detail', blog_id=blog_id))

@blog_bp.route('/user/<user_id>')
def user_blogs(user_id):
    """Kullanıcının blog yazıları route'u"""
    # Kullanıcı bilgilerini al
    from app.models.user import User
    author = User.get_by_id(user_id)
    if not author:
        abort(404)
        
    # Kullanıcının blog yazılarını al
    posts = Blog.get_by_author(user_id)
    
    return render_template('blog/user_blogs.html', 
                           author=author,
                           posts=posts, 
                           title="Kullanıcının Blog Yazıları")

@blog_bp.route('/my-posts')
@login_required
def my_posts():
    """Kullanıcının kendi blog yazılarını görüntüleme route'u"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    skip = (page - 1) * per_page
    
    # Kullanıcının blog yazılarını getir
    blogs = Blog.get_by_user(current_user.get_id(), limit=per_page, skip=skip)
    
    return render_template('blog/my_posts.html', 
                           blogs=blogs, 
                           title="Yazılarım",
                           page=page) 