from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask import abort, jsonify, current_app
from flask_login import login_required, current_user
from app.models.user import User, UserRole
from app.models.ctf import Challenge, Submission, Badge, UserBadge
from app.models.ctf import ChallengeCategory, ChallengeDifficulty
from app.extensions import mongo
from bson.objectid import ObjectId
from datetime import datetime
from functools import wraps
import os
import markdown
import bleach
import json

ctf = Blueprint('ctf', __name__, url_prefix='/ctf')

# Yetki kontrolü için decorator
def member_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_member and not current_user.is_admin):
            flash('Bu sayfaya erişim için Member yetkisi gerekiyor.', 'danger')
            return redirect(url_for('ctf.index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bu sayfaya erişim için admin yetkisi gerekiyor.', 'danger')
            return redirect(url_for('ctf.index'))
        return f(*args, **kwargs)
    return decorated_function

# Markdown içeriği dönüştürmek için yardımcı fonksiyon
def md_to_html(text):
    allowed_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'a', 'ul', 'ol', 'li', 
                    'strong', 'em', 'code', 'pre', 'blockquote', 'img', 'span', 'div', 'table', 
                    'thead', 'tbody', 'tr', 'th', 'td']
    allowed_attrs = {
        '*': ['class', 'style'],
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
    }
    html = markdown.markdown(text, extensions=['extra', 'codehilite', 'tables'])
    return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)

@ctf.route('/')
def index():
    # CTF ana sayfası - kategorileri ve istatistikleri göster
    categories = [c.value for c in ChallengeCategory]
    category_counts = {}
    for cat in categories:
        count = mongo.db.challenges.count_documents({"category": cat, "is_active": True})
        category_counts[cat] = count
        
    # İstatistikler
    total_challenges = mongo.db.challenges.count_documents({"is_active": True})
    total_submissions = mongo.db.submissions.count_documents({})
    total_correct_submissions = mongo.db.submissions.count_documents({"is_correct": True})
    
    # Kullanıcı başarıları
    if current_user.is_authenticated:
        user_solved = mongo.db.submissions.count_documents({
            "user_id": str(current_user._id),
            "is_correct": True
        })
        user_badges = UserBadge.get_by_user(str(current_user._id))
        badge_ids = [ub.badge_id for ub in user_badges]
        badges = [Badge.get_by_id(badge_id) for badge_id in badge_ids]
    else:
        user_solved = 0
        badges = []
    
    # Kullanıcı puanlarını hesapla
    user_points = 0
    if current_user.is_authenticated and current_user.is_member:
        solved_challenges = Challenge.get_solved_by_user(str(current_user._id))
        user_points = sum([challenge.points for challenge in solved_challenges])
    
    return render_template('ctf/index.html', 
                          categories=categories,
                          category_counts=category_counts,
                          stats={
                              'total_challenges': total_challenges,
                              'total_solves': total_correct_submissions,
                              'user_solves': user_solved,
                              'user_points': user_points
                          },
                          badges=badges)

@ctf.route('/challenges')
@login_required
@member_required
def challenges():
    # Tüm CTF görevlerini ve kategorileri listele
    category = request.args.get('category', None)
    difficulty = request.args.get('difficulty', None)
    
    # Kategori filtresi
    if category and category in [c.value for c in ChallengeCategory]:
        challenges_list = Challenge.get_all(only_active=True, category=category)
    else:
        challenges_list = Challenge.get_all(only_active=True)
    
    # Zorluk seviyesi filtresi
    if difficulty and difficulty in [d.value for d in ChallengeDifficulty]:
        challenges_list = [c for c in challenges_list if c.difficulty == difficulty]
        
    # Kullanıcının çözdüğü görevler
    solved_challenges = []
    if current_user.is_authenticated:
        user_submissions = Submission.get_correct_submissions_by_user(str(current_user._id))
        solved_challenges = [sub.challenge_id for sub in user_submissions]
    
    categories = [c.value for c in ChallengeCategory]
    difficulties = [d.value for d in ChallengeDifficulty]
    
    return render_template('ctf/challenges.html',
                          challenges=challenges_list,
                          categories=categories,
                          difficulties=difficulties,
                          solved_challenges=solved_challenges,
                          selected_category=category,
                          selected_difficulty=difficulty)

@ctf.route('/challenge/<challenge_id>')
@login_required
@member_required
def challenge_detail(challenge_id):
    # Belirli bir CTF görevini görüntüle
    challenge = Challenge.get_by_id(challenge_id)
    if not challenge:
        flash('Görev bulunamadı.', 'danger')
        return redirect(url_for('ctf.challenges'))
    
    # Markdown açıklamayı HTML'e dönüştür
    challenge.description_html = md_to_html(challenge.description)
    
    # Kullanıcının bu görevi çözüp çözmediğini kontrol et
    is_solved = False
    if current_user.is_authenticated:
        submission = Submission.get_by_user_and_challenge(str(current_user._id), str(challenge._id))
        is_solved = submission is not None
    
    # Çözüm sayısı
    solved_count = challenge.solved_count
    
    return render_template('ctf/challenge_detail.html',
                          challenge=challenge,
                          is_solved=is_solved,
                          solved_count=solved_count)

@ctf.route('/challenges/<challenge_id>/submit', methods=['POST'])
@login_required
def submit_flag(challenge_id):
    """Handle flag submission for a challenge."""
    flag = request.form.get('flag', '').strip()
    
    if not flag:
        flash('Bayrak boş olamaz!', 'warning')
        return redirect(url_for('ctf.challenge_detail', challenge_id=challenge_id))
    
    # Görevi kontrol et
    challenge = Challenge.get_by_id(challenge_id)
    if not challenge:
        flash('Görev bulunamadı!', 'danger')
        return redirect(url_for('ctf.challenges'))
    
    # Kullanıcı daha önce bu görevi doğru çözmüş mü?
    existing_submission = Submission.get_by_user_and_challenge(
        str(current_user._id), str(challenge._id)
    )
    
    if existing_submission and existing_submission.is_correct:
        flash('Bu görevi zaten çözdünüz!', 'info')
        return redirect(url_for('ctf.challenge_detail', challenge_id=challenge_id))
    
    # Flag'i kontrol et
    is_correct = (flag == challenge.flag)
    current_points = challenge.points if is_correct else 0
    
    # Submission oluştur
    submission = Submission(
        user_id=str(current_user._id),
        challenge_id=str(challenge._id),
        flag_submitted=flag,
        is_correct=is_correct,
        points=current_points
    )
    
    # Submission için tarihi ayarla
    submission.submitted_at = datetime.utcnow()
    
    # Kaydet
    submission.save()
    
    print(f"Debug - Submission created: user={current_user.username}, challenge={challenge.title}, points={current_points}, correct={is_correct}")
    
    if is_correct:
        flash('Tebrikler! Doğru bayrağı buldunuz.', 'success')
        
        # Kullanıcıya rozet vermek için kontrol et
        check_and_award_badges(str(current_user._id))
    else:
        flash('Yanlış bayrak. Tekrar deneyin!', 'danger')
    
    return redirect(url_for('ctf.challenge_detail', challenge_id=challenge_id))

@ctf.route('/scoreboard')
@login_required
def scoreboard():
    """Displays the CTF leaderboard."""
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # MongoDB aggregation pipeline for getting user scores
    pipeline = [
        {"$match": {"is_correct": True}},
        {"$group": {
            "_id": "$user_id", 
            "total_points": {"$sum": "$points"},
            "solved_count": {"$sum": 1},
            "last_solve": {"$max": "$submitted_at"}
        }},
        {"$sort": {"total_points": -1, "last_solve": 1}},
    ]
    
    try:
        # Doğru çözümlerin toplam sayısını yazdır (debug için)
        correct_submissions_count = mongo.db.submissions.count_documents({"is_correct": True})
        print(f"Debug - Total correct submissions count: {correct_submissions_count}")
        
        # MongoDB'den skorboard verilerini al
        scoreboard_data = list(mongo.db.submissions.aggregate(pipeline))
        print(f"Debug - Scoreboard data size: {len(scoreboard_data)}")
        
        # Eğer aggregation sonuç dönmezse manuel hesaplama yap
        if len(scoreboard_data) == 0 and correct_submissions_count > 0:
            print("Debug - Aggregation returned no results, calculating manually")
            
            # Tüm doğru çözümleri al
            correct_submissions = list(mongo.db.submissions.find({"is_correct": True}))
            
            # Kullanıcılar için toplam puanları hesapla
            user_totals = {}
            for sub in correct_submissions:
                user_id = sub.get("user_id")
                points = sub.get("points", 0)
                
                if user_id not in user_totals:
                    user_totals[user_id] = {
                        "_id": user_id,
                        "total_points": 0,
                        "solved_count": 0,
                        "last_solve": sub.get("submitted_at", datetime.utcnow())
                    }
                
                user_totals[user_id]["total_points"] += points
                user_totals[user_id]["solved_count"] += 1
                
                # Son çözüm tarihini güncelle
                sub_date = sub.get("submitted_at")
                if sub_date and (sub_date > user_totals[user_id]["last_solve"]):
                    user_totals[user_id]["last_solve"] = sub_date
            
            # Dict'i listeye dönüştür
            scoreboard_data = list(user_totals.values())
            
            # Toplam puana göre sırala, eşitlik durumunda son çözüm tarihine göre
            scoreboard_data.sort(key=lambda x: (-x["total_points"], x["last_solve"]))
        
        # Kullanıcı bilgileri ekle
        for entry in scoreboard_data:
            user = User.get_by_id(entry["_id"])
            if user:
                entry["username"] = user.username
                entry["is_admin"] = user.is_admin
                entry["is_member"] = user.is_member
            else:
                entry["username"] = "Deleted User"
                entry["is_admin"] = False
                entry["is_member"] = False
        
        total_users = len(scoreboard_data)
        total_pages = (total_users + per_page - 1) // per_page if total_users > 0 else 1
        
        skip = (page - 1) * per_page
        end = skip + per_page
        
        scoreboard = scoreboard_data[skip:end]
        
        # Kategori istatistikleri
        categories = [c.value for c in ChallengeCategory]
        category_stats = []
        
        for category_name in categories:
            # Kategori bazlı görevleri al
            challenges = list(mongo.db.challenges.find({"category": category_name}))
            
            if challenges:
                total_challenges = len(challenges)
                challenge_ids = [str(c["_id"]) for c in challenges]
                
                # Bu kategorideki çözülen görevleri say
                solved_challenges = mongo.db.submissions.aggregate([
                    {"$match": {
                        "challenge_id": {"$in": challenge_ids},
                        "is_correct": True
                    }},
                    {"$group": {"_id": "$challenge_id"}}
                ])
                
                solved_count = len(list(solved_challenges))
                solve_rate = (solved_count / total_challenges) * 100 if total_challenges > 0 else 0
                
                category_stats.append({
                    'name': category_name,
                    'total': total_challenges,
                    'solved': solved_count,
                    'solve_rate': solve_rate
                })
        
        # En çok çözülen görevler
        most_solved_pipeline = [
            {"$match": {"is_correct": True}},
            {"$group": {
                "_id": "$challenge_id", 
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        most_solved_results = list(mongo.db.submissions.aggregate(most_solved_pipeline))
        
        most_solved_data = []
        for result in most_solved_results:
            challenge = Challenge.get_by_id(result["_id"])
            if challenge:
                most_solved_data.append({
                    'challenge': challenge,
                    'solution_count': result["count"]
                })
        
    except Exception as e:
        print(f"Hata: {str(e)}")
        flash(f'Puan tablosu yüklenirken bir hata oluştu: {str(e)}', 'danger')
        return redirect(url_for('ctf.index'))
    
    return render_template(
        'ctf/scoreboard.html',
        scoreboard=scoreboard,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        category_stats=category_stats,
        most_solved_data=most_solved_data
    )

@ctf.route('/profile')
@login_required
@member_required
def profile():
    # Kullanıcının CTF profil sayfası
    # Çözülen görevler
    user_submissions = Submission.get_correct_submissions_by_user(str(current_user._id))
    challenge_ids = [sub.challenge_id for sub in user_submissions]
    solved_challenges = [Challenge.get_by_id(cid) for cid in challenge_ids]
    
    # Kategori başına istatistikler
    category_stats = {}
    for cat in [c.value for c in ChallengeCategory]:
        category_stats[cat] = len([c for c in solved_challenges if c and c.category == cat])
    
    # Zorluk seviyesi başına istatistikler
    difficulty_stats = {}
    for diff in [d.value for d in ChallengeDifficulty]:
        difficulty_stats[diff] = len([c for c in solved_challenges if c and c.difficulty == diff])
    
    # Toplam puan
    total_points = sum(sub.points for sub in user_submissions)
    
    # Rozetler
    user_badges = UserBadge.get_by_user(str(current_user._id))
    badge_ids = [ub.badge_id for ub in user_badges]
    badges = [Badge.get_by_id(badge_id) for badge_id in badge_ids]
    
    return render_template('ctf/profile.html',
                          user=current_user,
                          solved_challenges=solved_challenges,
                          category_stats=category_stats,
                          difficulty_stats=difficulty_stats,
                          total_points=total_points,
                          badges=badges)

# Admin routes
@ctf.route('/admin')
@login_required
@admin_required
def admin_ctf():
    # CTF yönetim paneli
    challenges_list = Challenge.get_all()
    badges_list = Badge.get_all()
    
    total_submissions = mongo.db.submissions.count_documents({})
    correct_submissions = mongo.db.submissions.count_documents({"is_correct": True})
    
    return render_template('ctf/admin/index.html',
                          challenges=challenges_list,
                          badges=badges_list,
                          total_submissions=total_submissions,
                          correct_submissions=correct_submissions)

@ctf.route('/admin/challenges/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_ctf_create_challenge():
    # Yeni CTF görevi oluştur
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        difficulty = request.form.get('difficulty')
        points = int(request.form.get('points', 0))
        flag = request.form.get('flag')
        
        # Hint'leri al
        hints = []
        for i in range(3):  # En fazla 3 hint
            hint = request.form.get(f'hint{i+1}')
            if hint:
                hints.append(hint)
        
        if not title or not description or not category or not difficulty or not flag:
            flash('Lütfen tüm gerekli alanları doldurun.', 'danger')
            return redirect(url_for('ctf.admin_ctf_create_challenge'))
        
        challenge = Challenge(
            title=title,
            description=description,
            category=category,
            difficulty=difficulty,
            points=points,
            flag=flag,
            hints=hints,
            created_by=str(current_user._id)
        )
        challenge.save()
        
        flash('CTF görevi başarıyla oluşturuldu.', 'success')
        return redirect(url_for('ctf.admin_ctf'))
    
    # GET metodu için form sayfasını göster
    categories = [c.value for c in ChallengeCategory]
    difficulties = [d.value for d in ChallengeDifficulty]
    
    return render_template('ctf/admin/create_challenge.html',
                          categories=categories,
                          difficulties=difficulties)

@ctf.route('/admin/challenges/<challenge_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_ctf_edit_challenge(challenge_id):
    # CTF görevini düzenle
    challenge = Challenge.get_by_id(challenge_id)
    
    if not challenge:
        flash('Görev bulunamadı.', 'danger')
        return redirect(url_for('ctf.admin_ctf'))
    
    if request.method == 'POST':
        challenge.title = request.form.get('title')
        challenge.description = request.form.get('description')
        challenge.category = request.form.get('category')
        challenge.difficulty = request.form.get('difficulty')
        challenge.points = int(request.form.get('points', 0))
        challenge.flag = request.form.get('flag')
        
        # Hint'leri güncelle
        hints = []
        for i in range(3):  # En fazla 3 hint
            hint = request.form.get(f'hint{i+1}')
            if hint:
                hints.append(hint)
        challenge.hints = hints
        
        # Aktif durumunu güncelle
        challenge.is_active = 'is_active' in request.form
        
        challenge.save()
        flash('CTF görevi başarıyla güncellendi.', 'success')
        return redirect(url_for('ctf.admin_ctf'))
    
    # GET metodu için düzenleme formunu göster
    categories = [c.value for c in ChallengeCategory]
    difficulties = [d.value for d in ChallengeDifficulty]
    
    return render_template('ctf/admin/edit_challenge.html',
                          challenge=challenge,
                          categories=categories,
                          difficulties=difficulties)

@ctf.route('/admin/challenges/<challenge_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_ctf_delete_challenge(challenge_id):
    # CTF görevini sil
    challenge = Challenge.get_by_id(challenge_id)
    
    if not challenge:
        flash('Görev bulunamadı.', 'danger')
        return redirect(url_for('ctf.admin_ctf'))
    
    challenge.delete()
    flash('CTF görevi başarıyla silindi.', 'success')
    return redirect(url_for('ctf.admin_ctf'))

@ctf.route('/admin/badges/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_ctf_create_badge():
    # Yeni rozet oluştur
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        criteria_type = request.form.get('criteria_type')
        criteria_value = request.form.get('criteria_value')
        
        if not name or not description or not criteria_type or not criteria_value:
            flash('Lütfen tüm gerekli alanları doldurun.', 'danger')
            return redirect(url_for('ctf.admin_ctf_create_badge'))
        
        # Kriter tipine göre kriterleri oluştur
        criteria = {}
        if criteria_type == 'min_points':
            criteria = {"min_points": int(criteria_value)}
        elif criteria_type == 'challenge_count':
            criteria = {"challenge_count": int(criteria_value)}
        elif criteria_type == 'category':
            criteria = {"category": criteria_value}
        
        badge = Badge(
            name=name,
            description=description,
            image_url=image_url,
            criteria=criteria,
            created_by=str(current_user._id)
        )
        badge.save()
        
        flash('Rozet başarıyla oluşturuldu.', 'success')
        return redirect(url_for('ctf.admin_ctf'))
    
    # GET metodu için form sayfasını göster
    categories = [c.value for c in ChallengeCategory]
    
    return render_template('ctf/admin/create_badge.html',
                          categories=categories)

@ctf.route('/admin/badges/<badge_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_ctf_edit_badge(badge_id):
    # Rozeti düzenle
    badge = Badge.get_by_id(badge_id)
    if not badge:
        flash('Rozet bulunamadı.', 'danger')
        return redirect(url_for('ctf.admin_ctf'))
    
    if request.method == 'POST':
        badge.name = request.form.get('name')
        badge.description = request.form.get('description')
        badge.image_url = request.form.get('image_url')
        
        criteria_type = request.form.get('criteria_type')
        criteria_value = request.form.get('criteria_value')
        
        # Kriter tipine göre kriterleri güncelle
        criteria = {}
        if criteria_type == 'min_points':
            criteria = {"min_points": int(criteria_value)}
        elif criteria_type == 'challenge_count':
            criteria = {"challenge_count": int(criteria_value)}
        elif criteria_type == 'category':
            criteria = {"category": criteria_value}
        
        badge.criteria = criteria
        badge.save()
        
        flash('Rozet başarıyla güncellendi.', 'success')
        return redirect(url_for('ctf.admin_ctf'))
    
    # GET metodu için düzenleme formunu göster
    categories = [c.value for c in ChallengeCategory]
    
    # Kriterleri form için hazırla
    criteria_type = None
    criteria_value = None
    
    if 'min_points' in badge.criteria:
        criteria_type = 'min_points'
        criteria_value = badge.criteria['min_points']
    elif 'challenge_count' in badge.criteria:
        criteria_type = 'challenge_count'
        criteria_value = badge.criteria['challenge_count']
    elif 'category' in badge.criteria:
        criteria_type = 'category'
        criteria_value = badge.criteria['category']
    
    return render_template('ctf/admin/edit_badge.html',
                          badge=badge,
                          categories=categories,
                          criteria_type=criteria_type,
                          criteria_value=criteria_value)

@ctf.route('/admin/badges/<badge_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_ctf_delete_badge(badge_id):
    # Rozeti sil
    badge = Badge.get_by_id(badge_id)
    if not badge:
        flash('Rozet bulunamadı.', 'danger')
        return redirect(url_for('ctf.admin_ctf'))
    
    badge.delete()
    # İlgili kullanıcı rozetlerini de sil
    mongo.db.user_badges.delete_many({"badge_id": badge_id})
    
    flash('Rozet başarıyla silindi.', 'success')
    return redirect(url_for('ctf.admin_ctf'))

# Yardımcı fonksiyon: Kullanıcıya rozet verilip verilmeyeceğini kontrol et
def check_and_award_badges(user_id):
    # Kullanıcının doğru çözümleri
    user_submissions = Submission.get_correct_submissions_by_user(user_id)
    
    # Kullanıcının toplam puanı
    total_points = sum(sub.points for sub in user_submissions)
    
    # Çözülen görevlerin sayısı
    challenge_count = len(user_submissions)
    
    # Kategori başına çözülen görev sayısı
    category_counts = {}
    for sub in user_submissions:
        challenge = Challenge.get_by_id(sub.challenge_id)
        if challenge:
            if challenge.category not in category_counts:
                category_counts[challenge.category] = 0
            category_counts[challenge.category] += 1
    
    # Tüm rozetleri al ve kriterleri kontrol et
    badges = Badge.get_all()
    for badge in badges:
        # Kullanıcının zaten bu rozeti olup olmadığını kontrol et
        existing_badge = UserBadge.get_by_user_and_badge(user_id, str(badge._id))
        if existing_badge:
            continue
        
        # Rozet kriterlerini kontrol et
        criteria_met = False
        
        if 'min_points' in badge.criteria and total_points >= badge.criteria['min_points']:
            criteria_met = True
        elif 'challenge_count' in badge.criteria and challenge_count >= badge.criteria['challenge_count']:
            criteria_met = True
        elif 'category' in badge.criteria and badge.criteria['category'] in category_counts:
            category = badge.criteria['category']
            if 'count' in badge.criteria:
                # Belirli bir kategoriden belirli sayıda görev çözme
                if category_counts[category] >= badge.criteria['count']:
                    criteria_met = True
            else:
                # Belirli bir kategoriden en az bir görev çözme
                criteria_met = True
        
        if criteria_met:
            # Rozeti kullanıcıya ver
            user_badge = UserBadge(
                user_id=user_id,
                badge_id=str(badge._id)
            )
            user_badge.save()
            flash(f'Tebrikler! "{badge.name}" rozetini kazandınız!', 'success') 