# Siber Topluluk Web Uygulaması

Flask ile geliştirilmiş, MVC mimarisine uygun bir web uygulaması.

## Özellikler

- Kullanıcı kayıt ve giriş sistemi
- Blog yazıları oluşturma, düzenleme ve silme
- Duyuru yönetimi
- Admin paneli
- Responsive tasarım (Bootstrap 5)

## Kurulum

1. Repoyu klonlayın:
```
git clone https://github.com/kullanici/siber_topluluk.git
cd siber_topluluk
```

2. Sanal ortam oluşturun ve aktifleştirin:
```
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Gerekli paketleri yükleyin:
```
pip install -r requirements.txt
```

4. MongoDB'yi kurun ve çalıştırın:
```
# MongoDB'yi başlatın
mongod
```

5. `.env` dosyasını düzenleyin:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=gizlianahtar
MONGODB_URI=mongodb://localhost:27017/siber_topluluk
DEBUG=True
```

6. Uygulamayı çalıştırın:
```
flask run
```

## Proje Yapısı

```
/siber_topluluk
├── /app
│   ├── /static
│   │   ├── /css
│   │   ├── /js
│   │   ├── /uploads
│   ├── /templates
│   ├── /models
│   │   ├── user.py
│   │   ├── blog.py
│   │   ├── announcement.py
│   ├── /routes
│   │   ├── auth_routes.py
│   │   ├── blog_routes.py
│   │   ├── admin_routes.py
│   │   ├── main_routes.py
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
├── /tests
├── /migrations
├── .env
├── requirements.txt
├── run.py
```

## Kullanım

1. Tarayıcınızda `http://localhost:5000` adresine gidin
2. Kayıt olun veya giriş yapın
3. Blog yazıları oluşturun, düzenleyin veya silin
4. Admin yetkisi ile duyurular ekleyin ve kullanıcıları yönetin

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. 