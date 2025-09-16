#!/usr/bin/env python3
"""
Seed script untuk menginisialisasi data awal CMS Desa
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User, Role
from app.models.content import Category
from app.models.setting import Setting

def create_roles():
    """Create default roles"""
    roles_data = [
        {
            'name': 'admin',
            'description': 'Administrator dengan akses penuh',
            'permissions': {
                "users": ["create", "read", "update", "delete"], 
                "content": ["create", "read", "update", "delete", "publish"], 
                "settings": ["read", "update"]
            }
        },
        {
            'name': 'editor',
            'description': 'Editor yang dapat meninjau dan menyetujui konten',
            'permissions': {
                "content": ["create", "read", "update", "delete", "review", "publish"]
            }
        },
        {
            'name': 'publisher',
            'description': 'Publisher yang dapat membuat dan mengedit draft',
            'permissions': {
                "content": ["create", "read", "update"]
            }
        },
        {
            'name': 'public',
            'description': 'Pengunjung umum',
            'permissions': {
                "content": ["read"]
            }
        }
    ]
    
    for role_data in roles_data:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(
                name=role_data['name'],
                description=role_data['description'],
                permissions=role_data['permissions']
            )
            db.session.add(role)
            print(f"Created role: {role_data['name']}")
        else:
            # Update existing role
            role.description = role_data['description']
            role.permissions = role_data['permissions']
            print(f"Updated role: {role_data['name']}")
    
    db.session.commit()

def create_categories():
    """Create default categories"""
    categories_data = [
        {'name': 'Berita', 'description': 'Berita dan informasi terkini desa', 'color': '#007bff'},
        {'name': 'Kegiatan', 'description': 'Kegiatan dan acara desa', 'color': '#28a745'},
        {'name': 'Pengumuman', 'description': 'Pengumuman resmi pemerintah desa', 'color': '#ffc107'},
        {'name': 'Layanan', 'description': 'Informasi layanan publik desa', 'color': '#17a2b8'}
    ]
    
    for i, cat_data in enumerate(categories_data):
        from slugify import slugify
        slug = slugify(cat_data['name'])
        
        category = Category.query.filter_by(slug=slug).first()
        if not category:
            category = Category(
                name=cat_data['name'],
                slug=slug,
                description=cat_data['description'],
                color=cat_data['color'],
                sort_order=i
            )
            db.session.add(category)
            print(f"Created category: {cat_data['name']}")
    
    db.session.commit()

def create_admin_user():
    """Create default admin user"""
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        print("Error: Admin role not found!")
        return
    
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@desa.go.id',
            full_name='Administrator Desa',
            role_id=admin_role.id
        )
        admin_user.set_password('admin123')  # Change this in production!
        db.session.add(admin_user)
        db.session.commit()
        print("Created admin user: admin / admin123")
    else:
        print("Admin user already exists")

def create_settings():
    """Create default settings"""
    settings_data = [
        {'key': 'site_name', 'value': 'Portal Desa Digital', 'type': 'string', 'description': 'Nama website desa', 'is_public': True},
        {'key': 'site_description', 'value': 'Sistem Informasi dan Layanan Desa', 'type': 'string', 'description': 'Deskripsi website desa', 'is_public': True},
        {'key': 'contact_email', 'value': 'info@desa.go.id', 'type': 'string', 'description': 'Email kontak desa', 'is_public': True},
        {'key': 'contact_phone', 'value': '021-12345678', 'type': 'string', 'description': 'Nomor telepon desa', 'is_public': True},
        {'key': 'address', 'value': 'Jl. Raya Desa No. 123', 'type': 'string', 'description': 'Alamat kantor desa', 'is_public': True},
        {'key': 'max_file_size', 'value': '5242880', 'type': 'integer', 'description': 'Maksimal ukuran file upload (bytes)', 'is_public': False},
        {'key': 'allowed_extensions', 'value': 'jpg,jpeg,png,gif', 'type': 'string', 'description': 'Ekstensi file yang diizinkan', 'is_public': False},
    ]
    
    for setting_data in settings_data:
        setting = Setting.query.filter_by(key=setting_data['key']).first()
        if not setting:
            setting = Setting(**setting_data)
            db.session.add(setting)
            print(f"Created setting: {setting_data['key']}")
    
    db.session.commit()

def main():
    """Main seeding function"""
    app = create_app('development')
    
    with app.app_context():
        print("Starting database seeding...")
        
        # Create tables
        db.create_all()
        
        # Seed data
        create_roles()
        create_categories()
        create_admin_user()
        create_settings()
        
        print("Database seeding completed!")
        print("\nDefault login credentials:")
        print("Username: admin")
        print("Password: admin123")
        print("\nPlease change the default password after first login!")

if __name__ == '__main__':
    main()