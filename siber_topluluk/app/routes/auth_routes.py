from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import mongo
from bson.objectid import ObjectId

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Kullanıcı kayıt route'u"""
    # Kullanıcı giriş yapmışsa ana sayfaya yönlendir
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Form verilerini al
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Verileri doğrula
        error = None
        if not username:
            error = 'Kullanıcı adı gerekli.'
        elif not email:
            error = 'E-posta adresi gerekli.'
        elif not password:
            error = 'Şifre gerekli.'
        elif password != confirm_password:
            error = 'Şifreler eşleşmiyor.'
        
        # E-posta ve kullanıcı adı kullanımda mı kontrol et
        if not error:
            if User.get_by_email(email):
                error = f"'{email}' zaten kullanımda."
            elif User.get_by_username(username):
                error = f"'{username}' kullanıcı adı zaten alınmış."
        
        # Kullanıcı e-posta adresini kontrol et
        if email.endswith('@samsun.edu.tr'):
            role = "member"
        else:
            role = "user"
        
        # Hata yoksa kullanıcıyı oluştur
        if not error:
            # Yeni kullanıcı oluştur
            new_user = User(username=username, email=email, password=password, role=role)
            new_user.save()
            
            # Kullanıcıyı giriş yap
            login_user(new_user)
            
            # Yönlendir
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('main.index'))
        
        # Hata durumunda flash mesaj göster
        flash(error, 'danger')
    
    return render_template('auth/register.html', title='Kayıt Ol')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Kullanıcı giriş route'u"""
    # Kullanıcı giriş yapmışsa ana sayfaya yönlendir
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Form verilerini al
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Kullanıcıyı bul
        user = User.get_by_email(email)
        
        # Kullanıcı adı ve şifre kontrol et
        if not user or not user.check_password(password):
            flash('Lütfen e-posta ve şifrenizi kontrol edin.', 'danger')
            return render_template('auth/login.html', title='Giriş Yap')
        
        # Kullanıcıyı giriş yap
        login_user(user, remember=remember)
        
        # Yönlendir
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        else:
            return redirect(url_for('main.index'))
    
    return render_template('auth/login.html', title='Giriş Yap')

@auth_bp.route('/logout')
@login_required
def logout():
    """Kullanıcı çıkış route'u"""
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Kullanıcı profil sayfası"""
    return render_template('auth/profile.html', title='Profilim')

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Kullanıcı profil düzenleme route'u"""
    if request.method == 'POST':
        # Form verilerini al
        username = request.form.get('username')
        email = request.form.get('email')
        
        # Verileri doğrula
        error = None
        if not username:
            error = 'Kullanıcı adı gerekli.'
        elif not email:
            error = 'E-posta adresi gerekli.'
        
        # Kullanıcı adı ve e-posta değiştirilmişse, kullanımda mı kontrol et
        if not error:
            if username != current_user.username and User.get_by_username(username):
                error = f"'{username}' kullanıcı adı zaten alınmış."
            elif email != current_user.email and User.get_by_email(email):
                error = f"'{email}' zaten kullanımda."
        
        # Hata yoksa kullanıcıyı güncelle
        if not error:
            current_user.username = username
            current_user.email = email
            current_user.save()
            
            flash('Profil başarıyla güncellendi.', 'success')
            return redirect(url_for('auth.profile'))
        
        # Hata durumunda flash mesaj göster
        flash(error, 'danger')
    
    return render_template('auth/edit_profile.html', title='Profili Düzenle')

@auth_bp.route('/password/change', methods=['GET', 'POST'])
@login_required
def change_password():
    """Şifre değiştirme route'u"""
    if request.method == 'POST':
        # Form verilerini al
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verileri doğrula
        error = None
        if not current_password:
            error = 'Mevcut şifre gerekli.'
        elif not new_password:
            error = 'Yeni şifre gerekli.'
        elif new_password != confirm_password:
            error = 'Şifreler eşleşmiyor.'
        elif not current_user.check_password(current_password):
            error = 'Mevcut şifre yanlış.'
        
        # Hata yoksa şifreyi güncelle
        if not error:
            current_user.password_hash = generate_password_hash(new_password)
            current_user.save()
            
            flash('Şifre başarıyla değiştirildi.', 'success')
            return redirect(url_for('auth.profile'))
        
        # Hata durumunda flash mesaj göster
        flash(error, 'danger')
    
    return render_template('auth/change_password.html', title='Şifre Değiştir') 