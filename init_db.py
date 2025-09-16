#!/usr/bin/env python3
"""
Database initialization script for Portal Desa Digital
This script creates the database tables and populates them with initial data.
"""

import os
import sys
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User, Role
from app.models.content import Content, Category
from app.models.setting import Setting
from app.models.audit import AuditLog

def init_database():
    """Initialize database with tables and default data"""
    print("🚀 Initializing Portal Desa Digital Database...")
    
    # Create application context
    app = create_app('development')
    
    with app.app_context():
        try:
            # Drop all tables (be careful in production!)
            print("📋 Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            print("🏗️  Creating database tables...")
            db.create_all()
            
            # Insert default roles
            print("👥 Creating default roles...")
            Role.insert_roles()
            
            # Insert default settings
            print("⚙️  Creating default settings...")
            Setting.insert_default_settings()
            
            # Create default categories
            print("📂 Creating default categories...")
            create_default_categories()
            
            # Create admin user
            print("👤 Creating admin user...")
            create_admin_user()
            
            # Create sample content (optional)
            print("📝 Creating sample content...")
            create_sample_content()
            
            # Commit all changes
            db.session.commit()
            
            print("✅ Database initialization completed successfully!")
            print("\n📊 Database Summary:")
            print(f"   - Roles: {Role.query.count()}")
            print(f"   - Users: {User.query.count()}")
            print(f"   - Categories: {Category.query.count()}")
            print(f"   - Content: {Content.query.count()}")
            print(f"   - Settings: {Setting.query.count()}")
            
            print("\n🔐 Admin Login Credentials:")
            print("   Username: admin")
            print("   Password: Admin123!")
            print("   Email: admin@desa.go.id")
            
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            db.session.rollback()
            sys.exit(1)

def create_default_categories():
    """Create default content categories"""
    categories = [
        {
            'name': 'Berita',
            'slug': 'berita',
            'description': 'Berita terkini dari desa',
            'color': '#007bff',
            'sort_order': 1
        },
        {
            'name': 'Pengumuman',
            'slug': 'pengumuman',
            'description': 'Pengumuman resmi dari pemerintah desa',
            'color': '#ffc107',
            'sort_order': 2
        },
        {
            'name': 'Kegiatan',
            'slug': 'kegiatan',
            'description': 'Kegiatan dan acara desa',
            'color': '#28a745',
            'sort_order': 3
        },
        {
            'name': 'Layanan',
            'slug': 'layanan',
            'description': 'Informasi layanan publik desa',
            'color': '#17a2b8',
            'sort_order': 4
        },
        {
            'name': 'Profil Desa',
            'slug': 'profil-desa',
            'description': 'Informasi profil dan sejarah desa',
            'color': '#6f42c1',
            'sort_order': 5
        }
    ]
    
    for cat_data in categories:
        existing = Category.query.filter_by(slug=cat_data['slug']).first()
        if not existing:
            category = Category(**cat_data)
            db.session.add(category)

def create_admin_user():
    """Create default admin user"""
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        print("❌ Admin role not found!")
        return
    
    # Check if admin user already exists
    existing_admin = User.query.filter_by(username='admin').first()
    if existing_admin:
        print("ℹ️  Admin user already exists, skipping creation.")
        return
    
    admin_user = User(
        username='admin',
        email='admin@desa.go.id',
        full_name='Administrator Desa',
        phone='021-12345678',
        bio='Administrator sistem Portal Desa Digital',
        role_id=admin_role.id,
        status='active'
    )
    admin_user.set_password('Admin123!')
    
    db.session.add(admin_user)

def create_sample_content():
    """Create sample content for demonstration"""
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("❌ Admin user not found, skipping sample content creation.")
        return
    
    # Get categories
    berita_cat = Category.query.filter_by(slug='berita').first()
    pengumuman_cat = Category.query.filter_by(slug='pengumuman').first()
    kegiatan_cat = Category.query.filter_by(slug='kegiatan').first()
    
    sample_contents = [
        {
            'title': 'Selamat Datang di Portal Desa Digital',
            'slug': 'selamat-datang-portal-desa-digital',
            'excerpt': 'Portal Desa Digital hadir untuk memberikan informasi terkini dan layanan terbaik bagi masyarakat desa.',
            'content': '''
            <p>Selamat datang di Portal Desa Digital, platform informasi dan layanan terpadu untuk masyarakat desa. 
            Melalui portal ini, Anda dapat mengakses berbagai informasi penting seperti berita terkini, pengumuman resmi, 
            jadwal kegiatan, dan berbagai layanan publik yang tersedia.</p>
            
            <p>Portal ini dikembangkan dengan tujuan meningkatkan transparansi pemerintahan desa dan memudahkan akses 
            informasi bagi seluruh masyarakat. Kami berkomitmen untuk terus memberikan pelayanan terbaik dan informasi 
            yang akurat serta terkini.</p>
            
            <p>Terima kasih atas kunjungan Anda. Mari bersama-sama membangun desa yang lebih maju dan sejahtera!</p>
            ''',
            'category_id': berita_cat.id if berita_cat else None,
            'status': 'published',
            'published_at': datetime.utcnow()
        },
        {
            'title': 'Pengumuman Jadwal Pelayanan Administrasi',
            'slug': 'pengumuman-jadwal-pelayanan-administrasi',
            'excerpt': 'Informasi jadwal pelayanan administrasi kependudukan di kantor desa.',
            'content': '''
            <p>Kepada seluruh masyarakat desa, dengan ini kami informasikan jadwal pelayanan administrasi kependudukan:</p>
            
            <ul>
                <li><strong>Senin - Kamis:</strong> 08.00 - 15.00 WIB</li>
                <li><strong>Jumat:</strong> 08.00 - 11.30 WIB</li>
                <li><strong>Sabtu - Minggu:</strong> Libur</li>
            </ul>
            
            <p>Layanan yang tersedia meliputi:</p>
            <ul>
                <li>Pembuatan KTP</li>
                <li>Pembuatan Kartu Keluarga</li>
                <li>Surat Keterangan Domisili</li>
                <li>Surat Keterangan Usaha</li>
                <li>Dan layanan administrasi lainnya</li>
            </ul>
            
            <p>Untuk informasi lebih lanjut, silakan hubungi kantor desa di nomor (021) 12345678.</p>
            ''',
            'category_id': pengumuman_cat.id if pengumuman_cat else None,
            'status': 'published',
            'published_at': datetime.utcnow()
        },
        {
            'title': 'Gotong Royong Pembersihan Lingkungan',
            'slug': 'gotong-royong-pembersihan-lingkungan',
            'excerpt': 'Kegiatan gotong royong pembersihan lingkungan desa akan dilaksanakan pada hari Minggu mendatang.',
            'content': '''
            <p>Dalam rangka menjaga kebersihan dan keindahan lingkungan desa, akan dilaksanakan kegiatan gotong royong 
            pembersihan lingkungan dengan detail sebagai berikut:</p>
            
            <p><strong>Waktu:</strong> Minggu, 25 Februari 2024<br>
            <strong>Jam:</strong> 07.00 - 10.00 WIB<br>
            <strong>Tempat:</strong> Seluruh wilayah desa</p>
            
            <p>Kegiatan ini meliputi:</p>
            <ul>
                <li>Pembersihan jalan dan selokan</li>
                <li>Penataan taman desa</li>
                <li>Pengecatan fasilitas umum</li>
                <li>Penanaman pohon</li>
            </ul>
            
            <p>Seluruh masyarakat diharapkan dapat berpartisipasi aktif dalam kegiatan ini. 
            Mari bersama-sama menjaga kebersihan dan keindahan desa kita!</p>
            ''',
            'category_id': kegiatan_cat.id if kegiatan_cat else None,
            'status': 'published',
            'published_at': datetime.utcnow()
        }
    ]
    
    for content_data in sample_contents:
        existing = Content.query.filter_by(slug=content_data['slug']).first()
        if not existing:
            content = Content(
                author_id=admin_user.id,
                **content_data
            )
            db.session.add(content)

if __name__ == '__main__':
    print("Portal Desa Digital - Database Initialization")
    print("=" * 50)
    
    # Confirm before proceeding
    response = input("⚠️  This will drop all existing data. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Database initialization cancelled.")
        sys.exit(0)
    
    init_database()