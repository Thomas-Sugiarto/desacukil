# 🚀 Panduan Menjalankan CMS Desa

## Langkah-langkah untuk Menjalankan Project

### 1. **Persiapan Environment**
```bash
# Pastikan Python 3.8+ sudah terinstall
python --version

# Masuk ke direktori project
cd /workspace/cms_desa

# Aktifkan virtual environment (jika ada)
# source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows
```

### 2. **Install Dependencies**
```bash
# Install semua package yang dibutuhkan
pip install -r requirements.txt
```

### 3. **Setup Database**
```bash
# Set environment variable untuk Flask
export FLASK_APP=run.py
export FLASK_ENV=development

# Inisialisasi database (jika belum ada)
flask db init

# Buat migration untuk tabel
flask db migrate -m "Initial migration"

# Apply migration ke database
flask db upgrade
```

### 4. **Setup Data Awal**
```bash
# Jalankan script untuk membuat data awal (user admin, kategori, dll)
python scripts/init_data.py
```

### 5. **Menjalankan Aplikasi**

#### **Cara 1: Flask Development Server**
```bash
# Jalankan server development
flask run

# Atau dengan port khusus
flask run --port 5000 --host 0.0.0.0
```

#### **Cara 2: Python Script**
```bash
# Jalankan langsung dengan python
python run.py
```

#### **Cara 3: Gunicorn (Production)**
```bash
# Install gunicorn jika belum ada
pip install gunicorn

# Jalankan dengan gunicorn
gunicorn --config gunicorn.conf.py run:app
```

### 6. **Akses Aplikasi**

Buka browser dan akses:
- **Website Publik**: http://localhost:5000
- **Login Admin**: http://localhost:5000/auth/login

**Default Login:**
- **Admin**: username: `admin`, password: `admin123`
- **Editor**: username: `editor`, password: `editor123`  
- **Publisher**: username: `publisher`, password: `publisher123`

### 7. **Struktur URL Aplikasi**

```
├── /                          # Halaman utama website
├── /auth/login               # Login page
├── /admin/dashboard          # Dashboard admin
├── /editor/dashboard         # Dashboard editor
├── /publisher/dashboard      # Dashboard publisher
├── /berita                   # Kategori berita
├── /kegiatan                 # Kategori kegiatan
├── /search                   # Pencarian
└── /contact                  # Kontak
```

## 🔧 Troubleshooting

### **Error: "AssertionError: View function mapping is overwriting"**
**Solusi**: Error ini sudah diperbaiki dengan memisahkan route `/` di setiap blueprint.

### **Error: Database tidak ditemukan**
```bash
# Hapus folder migrations dan database
rm -rf migrations/
rm instance/cms_desa.db

# Inisialisasi ulang
flask db init
flask db migrate -m "Initial migration"  
flask db upgrade
python scripts/init_data.py
```

### **Error: ModuleNotFoundError**
```bash
# Install ulang dependencies
pip install -r requirements.txt

# Atau install satu per satu
pip install flask flask-sqlalchemy flask-migrate flask-login flask-wtf
```

### **Error: Permission denied**
```bash
# Berikan permission pada folder uploads
chmod -R 755 app/static/uploads/
```

## 🐳 Menjalankan dengan Docker

### **1. Build Docker Image**
```bash
cd /workspace/cms_desa
docker build -f docker/Dockerfile -t cms-desa .
```

### **2. Jalankan dengan Docker Compose**
```bash
# Jalankan semua services (web, database, redis)
docker-compose -f docker/docker-compose.yml up -d

# Lihat logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

## 📝 Testing

### **1. Jalankan Unit Tests**
```bash
# Jalankan semua test
python -m pytest tests/ -v

# Jalankan test spesifik
python -m pytest tests/test_auth.py -v
```

### **2. Manual Testing**
1. Buka http://localhost:5000
2. Login sebagai admin
3. Buat kategori baru
4. Login sebagai publisher
5. Buat konten baru
6. Login sebagai editor
7. Review dan approve konten
8. Cek konten muncul di website publik

## 🔒 Security Notes

- Ubah `SECRET_KEY` di production
- Gunakan database PostgreSQL untuk production
- Setup HTTPS dengan SSL certificate
- Konfigurasi rate limiting untuk production
- Backup database secara berkala

## 📚 Dokumentasi Tambahan

- **API Documentation**: `/api/docs` (jika diaktifkan)
- **Admin Panel**: `/admin/dashboard`
- **Database Schema**: Lihat file `models/`
- **Configuration**: File `config.py`

---

**🎉 Selamat! CMS Desa sudah siap digunakan!**

Jika ada masalah, periksa:
1. Log aplikasi di terminal
2. File log di folder `logs/`
3. Database connection
4. Permission folder uploads