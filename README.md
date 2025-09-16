# CMS Desa - Sistem Manajemen Konten Desa

Sistem manajemen konten berbasis Flask untuk website desa dengan workflow publikasi bertingkat dan manajemen role yang komprehensif.

## Fitur Utama

- **Multi-Role Authentication**: Admin, Editor, Publisher, dan Public dengan permission yang berbeda
- **Content Workflow**: Draft → Pending Review → Published/Rejected
- **Media Management**: Upload cover image dan embed YouTube
- **Security**: CSRF protection, password hashing, input validation
- **Responsive Design**: Bootstrap 5 dengan tema hijau formal
- **Audit Trail**: Log semua aktivitas user

## Role dan Permission

### Admin
- Kelola semua user dan role
- CRUD konten tanpa batasan
- Konfigurasi sistem
- Akses audit log

### Editor
- Review dan approve/reject konten
- CRUD konten
- Kelola kategori

### Publisher
- Buat dan edit draft sendiri
- Submit konten untuk review
- Tidak bisa langsung publish

### Public/Guest
- Hanya dapat melihat konten published

## Teknologi

- **Backend**: Flask 2.3+, SQLAlchemy, PostgreSQL
- **Frontend**: Bootstrap 5, jQuery
- **Security**: Flask-WTF, Flask-Login, Werkzeug
- **Deployment**: Gunicorn, Nginx

## Instalasi

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis (optional, untuk caching)

### Setup Development

1. **Clone repository**
```bash
git clone <repository-url>
cd cms_desa
```

2. **Buat virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup database PostgreSQL**
```bash
# Buat database
createdb cms_desa_dev

# Atau menggunakan psql
psql -U postgres
CREATE DATABASE cms_desa_dev;
\q
```

5. **Konfigurasi environment**
```bash
cp .env.example .env
# Edit .env sesuai konfigurasi Anda
```

6. **Setup database dan seed data**
```bash
# Inisialisasi migrasi
flask db init

# Buat migrasi pertama
flask db migrate -m "Initial migration"

# Jalankan migrasi
flask db upgrade

# Seed data awal
python scripts/seed_data.py
```

7. **Jalankan aplikasi**
```bash
python run.py
```

Aplikasi akan berjalan di `http://localhost:5000`

### Login Default
- **Username**: admin
- **Password**: admin123

**⚠️ PENTING: Ubah password default setelah login pertama!**

## Struktur Project

```
cms_desa/
├── app/
│   ├── blueprints/          # Blueprint untuk setiap role
│   │   ├── auth/           # Authentication
│   │   ├── admin/          # Admin management
│   │   ├── editor/         # Editor workflow
│   │   ├── publisher/      # Publisher content creation
│   │   └── public/         # Public website
│   ├── models/             # Database models
│   ├── core/               # Core utilities
│   ├── static/             # CSS, JS, images
│   └── templates/          # HTML templates
├── migrations/             # Database migrations
├── scripts/               # Utility scripts
├── tests/                 # Unit tests
├── config.py              # Configuration
├── requirements.txt       # Python dependencies
└── run.py                # Application entry point
```

## Workflow Konten

1. **Publisher** membuat draft konten
2. **Publisher** submit draft untuk review
3. **Editor** review konten:
   - Approve → Status menjadi "Published"
   - Reject → Status menjadi "Rejected" dengan komentar
4. Konten published tampil di website publik

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/profile` - User profile

### Admin
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - Kelola user
- `GET /admin/settings` - Pengaturan sistem

### Editor
- `GET /editor/dashboard` - Editor dashboard
- `GET /editor/pending` - Konten pending review
- `POST /editor/content/<id>/approve` - Approve konten

### Publisher
- `GET /publisher/dashboard` - Publisher dashboard
- `POST /publisher/content/create` - Buat konten baru
- `POST /publisher/content/<id>/submit` - Submit untuk review

### Public
- `GET /` - Homepage
- `GET /berita` - Daftar berita
- `GET /content/<slug>` - Detail konten

## Deployment Production

### Menggunakan Docker

1. **Build image**
```bash
docker build -t cms-desa .
```

2. **Jalankan dengan docker-compose**
```bash
docker-compose up -d
```

### Manual Deployment

1. **Setup server (Ubuntu/CentOS)**
```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv postgresql nginx

# Setup PostgreSQL
sudo -u postgres createdb cms_desa
```

2. **Deploy aplikasi**
```bash
# Clone dan setup
git clone <repository-url> /var/www/cms_desa
cd /var/www/cms_desa
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup database
flask db upgrade
python scripts/seed_data.py
```

3. **Konfigurasi Gunicorn**
```bash
# Install gunicorn
pip install gunicorn

# Test gunicorn
gunicorn --bind 0.0.0.0:8000 run:app
```

4. **Konfigurasi Nginx**
```bash
# Copy konfigurasi nginx
sudo cp deployment/nginx.conf /etc/nginx/sites-available/cms_desa
sudo ln -s /etc/nginx/sites-available/cms_desa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

5. **Setup Systemd Service**
```bash
sudo cp deployment/cms_desa.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cms_desa
sudo systemctl start cms_desa
```

## Konfigurasi Environment

### Development (.env)
```
FLASK_ENV=development
DATABASE_URL=postgresql://user:pass@localhost/cms_desa_dev
SECRET_KEY=your-secret-key
```

### Production (.env)
```
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost/cms_desa
SECRET_KEY=your-production-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
```

## Testing

```bash
# Jalankan tests
python -m pytest tests/

# Test dengan coverage
python -m pytest --cov=app tests/
```

## Backup Database

```bash
# Manual backup
pg_dump cms_desa > backup_$(date +%Y%m%d_%H%M%S).sql

# Menggunakan script
python scripts/backup.py
```

## Troubleshooting

### Error Database Connection
```bash
# Cek status PostgreSQL
sudo systemctl status postgresql

# Cek konfigurasi database
psql -U postgres -l
```

### Error Permission
```bash
# Cek permission file
ls -la app/static/uploads/

# Set permission yang benar
chmod 755 app/static/uploads/
```

### Error Nginx
```bash
# Cek konfigurasi nginx
sudo nginx -t

# Cek log error
sudo tail -f /var/log/nginx/error.log
```

## Kontribusi

1. Fork repository
2. Buat feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buat Pull Request

## Lisensi

Project ini menggunakan lisensi MIT. Lihat file `LICENSE` untuk detail.

## Support

Untuk pertanyaan dan support:
- Email: support@desa.go.id
- Documentation: [Wiki](link-to-wiki)
- Issues: [GitHub Issues](link-to-issues)

---

**Dibuat dengan ❤️ untuk kemajuan digitalisasi desa di Indonesia**