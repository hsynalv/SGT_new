from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app.models import Course, Lesson, Enrollment, UserRole
from app.extensions import mongo
from bson.objectid import ObjectId
from functools import wraps

courses = Blueprint('courses', __name__)

# Yetki kontrolü için decorator
def member_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_member:
            flash('Bu sayfaya erişim için Member yetkisi gerekiyor.', 'danger')
            return redirect(url_for('courses.index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bu sayfaya erişim için Admin yetkisi gerekiyor.', 'danger')
            return redirect(url_for('courses.index'))
        return f(*args, **kwargs)
    return decorated_function

# Tüm kursları listeleyen sayfa
@courses.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    limit = 6
    skip = (page - 1) * limit
    courses_list = Course.get_all(skip=skip, limit=limit)
    return render_template('courses/index.html', courses=courses_list, page=page)

# Kurs detaylarını gösteren sayfa
@courses.route('/<course_id>')
def detail(course_id):
    course = Course.get_by_id(course_id)
    if not course:
        abort(404)
    
    # Kullanıcı oturum açmışsa, kursa kaydolup olmadığını kontrol et
    enrollment = None
    if current_user.is_authenticated:
        enrollment = Enrollment.get_by_user_and_course(current_user.get_id(), str(course._id))
    
    # Kursa ait dersleri getir
    lessons = Lesson.get_by_course(str(course._id))
    
    # Kursa kayıtlı öğrenci sayısını hesapla
    enrolled_users_count = Enrollment.get_count_by_course(str(course._id))
    
    return render_template('courses/detail.html', 
                          course=course, 
                          lessons=lessons, 
                          enrollment=enrollment,
                          enrolled_users_count=enrolled_users_count)

# Kursa kaydolma işlemi
@courses.route('/<course_id>/enroll', methods=['POST'])
@login_required
@member_required
def enroll(course_id):
    course = Course.get_by_id(course_id)
    if not course:
        abort(404)
    
    # Kullanıcı zaten kayıtlı mı kontrol et
    existing_enrollment = Enrollment.get_by_user_and_course(current_user.get_id(), str(course._id))
    if existing_enrollment:
        flash('Bu kursa zaten kayıtlısınız.', 'info')
        return redirect(url_for('courses.detail', course_id=course_id))
    
    # Yeni kayıt oluştur
    enrollment = Enrollment(
        user_id=current_user.get_id(),
        course_id=str(course._id)
    )
    enrollment.save()
    
    flash('Kursa başarıyla kaydoldunuz!', 'success')
    return redirect(url_for('courses.detail', course_id=course_id))

# Ders içeriği gösterme sayfası (yalnızca kayıtlı öğrenciler için)
@courses.route('/<course_id>/lessons/<lesson_id>')
@login_required
@member_required
def lesson_detail(course_id, lesson_id):
    course = Course.get_by_id(course_id)
    lesson = Lesson.get_by_id(lesson_id)
    
    if not course or not lesson:
        abort(404)
    
    # Kullanıcının kursa kaydı var mı kontrol et
    enrollment = Enrollment.get_by_user_and_course(current_user.get_id(), str(course._id))
    if not enrollment and not current_user.is_admin:
        flash('Bu dersi görüntülemek için kursa kaydolmalısınız.', 'warning')
        return redirect(url_for('courses.detail', course_id=course_id))
    
    # Kursa ait tüm dersleri getir (navigasyon için)
    lessons = Lesson.get_by_course(str(course._id))
    
    return render_template('courses/lesson.html', 
                          course=course, 
                          lesson=lesson, 
                          lessons=lessons, 
                          enrollment=enrollment)

# İlerleme güncelleme (AJAX)
@courses.route('/<course_id>/progress', methods=['POST'])
@login_required
@member_required
def update_progress(course_id):
    progress = request.json.get('progress', 0)
    
    enrollment = Enrollment.get_by_user_and_course(current_user.get_id(), course_id)
    if not enrollment:
        return jsonify({'success': False, 'message': 'Enrollment not found'}), 404
    
    enrollment.update_progress(progress)
    return jsonify({'success': True, 'progress': enrollment.progress})

# Kurs oluşturma (sadece adminler için)
@courses.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        instructor = request.form.get('instructor')
        level = request.form.get('level')
        tags = request.form.get('tags', '').split(',')
        
        if not title or not description:
            flash('Başlık ve açıklama alanları zorunludur.', 'danger')
            return render_template('courses/create.html')
        
        course = Course(
            title=title,
            description=description,
            image_url=image_url,
            instructor=instructor,
            level=level,
            tags=[tag.strip() for tag in tags if tag.strip()],
            created_by=current_user.get_id()
        )
        course.save()
        
        flash('Kurs başarıyla oluşturuldu!', 'success')
        return redirect(url_for('courses.detail', course_id=course._id))
    
    return render_template('courses/create.html')

# Kurs düzenleme (sadece adminler için)
@courses.route('/<course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(course_id):
    course = Course.get_by_id(course_id)
    if not course:
        abort(404)
    
    if request.method == 'POST':
        course.title = request.form.get('title')
        course.description = request.form.get('description')
        course.image_url = request.form.get('image_url')
        course.instructor = request.form.get('instructor')
        course.level = request.form.get('level')
        course.tags = [tag.strip() for tag in request.form.get('tags', '').split(',') if tag.strip()]
        
        course.save()
        flash('Kurs başarıyla güncellendi!', 'success')
        return redirect(url_for('courses.detail', course_id=course._id))
    
    return render_template('courses/edit.html', course=course)

# Kurs silme (sadece adminler için)
@courses.route('/<course_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(course_id):
    course = Course.get_by_id(course_id)
    if not course:
        abort(404)
    
    course.delete()
    flash('Kurs başarıyla silindi!', 'success')
    return redirect(url_for('courses.index'))

# Ders oluşturma (sadece adminler için)
@courses.route('/<course_id>/lessons/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_lesson(course_id):
    course = Course.get_by_id(course_id)
    if not course:
        abort(404)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        video_url = request.form.get('video_url')
        order = request.form.get('order', 0, type=int)
        duration = request.form.get('duration')
        
        if not title or not video_url:
            flash('Başlık ve video URL alanları zorunludur.', 'danger')
            return render_template('courses/create_lesson.html', course=course)
        
        lesson = Lesson(
            title=title,
            description=description,
            video_url=video_url,
            course_id=str(course._id),
            order=order,
            duration=duration
        )
        lesson.save()
        
        flash('Ders başarıyla oluşturuldu!', 'success')
        return redirect(url_for('courses.detail', course_id=course._id))
    
    # Var olan ders sayısını al ve 1 ekle (önerilen sıra için)
    existing_lessons = Lesson.get_by_course(str(course._id))
    suggested_order = len(existing_lessons) + 1
    
    return render_template('courses/create_lesson.html', 
                          course=course, 
                          suggested_order=suggested_order)

# Ders düzenleme (sadece adminler için)
@courses.route('/<course_id>/lessons/<lesson_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lesson(course_id, lesson_id):
    course = Course.get_by_id(course_id)
    lesson = Lesson.get_by_id(lesson_id)
    
    if not course or not lesson:
        abort(404)
    
    if request.method == 'POST':
        lesson.title = request.form.get('title')
        lesson.description = request.form.get('description')
        lesson.video_url = request.form.get('video_url')
        lesson.order = request.form.get('order', 0, type=int)
        lesson.duration = request.form.get('duration')
        
        lesson.save()
        flash('Ders başarıyla güncellendi!', 'success')
        return redirect(url_for('courses.detail', course_id=course._id))
    
    return render_template('courses/edit_lesson.html', 
                          course=course,
                          lesson=lesson)

# Kursun derslerini listeleyen sayfa (adminler için)
@courses.route('/<course_id>/lessons')
@login_required
@admin_required
def lessons(course_id):
    course = Course.get_by_id(course_id)
    if not course:
        abort(404)
    
    lessons = Lesson.get_by_course(str(course._id))
    return render_template('courses/lessons.html', 
                          course=course,
                          lessons=lessons)

# Ders silme (sadece adminler için)
@courses.route('/<course_id>/lessons/<lesson_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_lesson(course_id, lesson_id):
    course = Course.get_by_id(course_id)
    lesson = Lesson.get_by_id(lesson_id)
    
    if not course or not lesson:
        abort(404)
    
    lesson.delete()
    flash('Ders başarıyla silindi!', 'success')
    return redirect(url_for('courses.detail', course_id=course._id))

# Kullanıcının kayıtlı olduğu kursları listeleyen sayfa
@courses.route('/enrolled')
@login_required
@member_required
def enrolled_courses():
    # Kullanıcının kayıtlı olduğu kursları bul
    enrollments = Enrollment.get_by_user(current_user.get_id())
    course_ids = [enrollment.course_id for enrollment in enrollments]
    
    # Kurs detaylarını al
    courses_list = []
    for course_id in course_ids:
        course = Course.get_by_id(course_id)
        if course:
            courses_list.append(course)
    
    return render_template('courses/enrolled.html',
                           courses=courses_list,
                           enrollments={e.course_id: e for e in enrollments},
                           title='Kayıtlı Kurslarım') 