from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db

class Setting(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    type = db.Column(db.String(20), default='string')
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Setting {self.key}>'
    
    @staticmethod
    def get_value(key, default=None):
        """Get setting value by key"""
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            # Convert value based on type
            if setting.type == 'integer':
                try:
                    return int(setting.value)
                except (ValueError, TypeError):
                    return default
            elif setting.type == 'boolean':
                return setting.value.lower() in ['true', '1', 'yes', 'on']
            elif setting.type == 'json':
                try:
                    import json
                    return json.loads(setting.value)
                except (ValueError, TypeError):
                    return default
            else:
                return setting.value
        return default
    
    @staticmethod
    def set_value(key, value, type='string', description=None, is_public=False):
        """Set setting value"""
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
            setting.type = type
            if description:
                setting.description = description
            setting.is_public = is_public
            setting.updated_at = datetime.utcnow()
        else:
            setting = Setting(
                key=key,
                value=str(value),
                type=type,
                description=description,
                is_public=is_public
            )
            db.session.add(setting)
        
        return setting
    
    @staticmethod
    def get_public_settings():
        """Get all public settings"""
        settings = Setting.query.filter_by(is_public=True).all()
        return {s.key: Setting.get_value(s.key) for s in settings}
    
    @staticmethod
    def insert_default_settings():
        """Insert default settings"""
        default_settings = {
            'site_name': {
                'value': 'Portal Desa Digital',
                'type': 'string',
                'description': 'Nama website desa',
                'is_public': True
            },
            'site_description': {
                'value': 'Sistem Informasi dan Layanan Desa',
                'type': 'string',
                'description': 'Deskripsi website desa',
                'is_public': True
            },
            'contact_email': {
                'value': 'info@desa.go.id',
                'type': 'string',
                'description': 'Email kontak desa',
                'is_public': True
            },
            'contact_phone': {
                'value': '021-12345678',
                'type': 'string',
                'description': 'Nomor telepon desa',
                'is_public': True
            },
            'address': {
                'value': 'Jl. Raya Desa No. 123',
                'type': 'string',
                'description': 'Alamat kantor desa',
                'is_public': True
            },
            'posts_per_page': {
                'value': '10',
                'type': 'integer',
                'description': 'Jumlah post per halaman',
                'is_public': False
            },
            'allow_registration': {
                'value': 'false',
                'type': 'boolean',
                'description': 'Izinkan registrasi publik',
                'is_public': False
            }
        }
        
        for key, setting_data in default_settings.items():
            existing = Setting.query.filter_by(key=key).first()
            if not existing:
                Setting.set_value(
                    key=key,
                    value=setting_data['value'],
                    type=setting_data['type'],
                    description=setting_data['description'],
                    is_public=setting_data['is_public']
                )
        
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'type': self.type,
            'description': self.description,
            'is_public': self.is_public,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }