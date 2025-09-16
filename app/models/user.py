from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
from app import db

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.JSON, default={})
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def has_permission(self, resource, action):
        """Check if role has specific permission"""
        if not self.permissions:
            return False
        
        resource_perms = self.permissions.get(resource, [])
        return action in resource_perms
    
    @staticmethod
    def insert_roles():
        """Insert default roles"""
        roles = {
            'admin': {
                'description': 'Administrator dengan akses penuh',
                'permissions': {
                    'users': ['create', 'read', 'update', 'delete'],
                    'content': ['create', 'read', 'update', 'delete', 'publish'],
                    'categories': ['create', 'read', 'update', 'delete'],
                    'settings': ['read', 'update'],
                    'audit': ['read']
                }
            },
            'editor': {
                'description': 'Editor yang dapat mengelola dan mereview konten',
                'permissions': {
                    'content': ['create', 'read', 'update', 'delete', 'publish', 'review'],
                    'categories': ['read']
                }
            },
            'publisher': {
                'description': 'Publisher yang dapat membuat konten',
                'permissions': {
                    'content': ['create', 'read', 'update'],
                    'categories': ['read']
                }
            }
        }
        
        for role_name, role_data in roles.items():
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(
                    name=role_name,
                    description=role_data['description'],
                    permissions=role_data['permissions']
                )
                db.session.add(role)
            else:
                # Update existing role permissions
                role.description = role_data['description']
                role.permissions = role_data['permissions']
        
        db.session.commit()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    status = db.Column(db.String(20), default='active')
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    authored_content = db.relationship('Content', foreign_keys='Content.author_id', backref='author', lazy='dynamic')
    reviewed_content = db.relationship('Content', foreign_keys='Content.reviewer_id', backref='reviewer', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, resource, action):
        """Check if user has specific permission"""
        return self.role.has_permission(resource, action)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role.name == 'admin'
    
    def is_editor(self):
        """Check if user is editor"""
        return self.role.name in ['admin', 'editor']
    
    def is_publisher(self):
        """Check if user is publisher"""
        return self.role.name in ['admin', 'editor', 'publisher']
    
    def to_dict(self):
        """Convert user to dictionary with safe string handling"""
        try:
            return {
                'id': self.id,
                'username': str(self.username) if self.username else '',
                'email': str(self.email) if self.email else '',
                'full_name': str(self.full_name) if self.full_name else '',
                'phone': str(self.phone) if self.phone else '',
                'bio': str(self.bio) if self.bio else '',
                'role': str(self.role.name) if self.role else '',
                'status': str(self.status) if self.status else 'active',
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'last_login': self.last_login.isoformat() if self.last_login else None
            }
        except Exception as e:
            # Fallback dictionary with minimal safe data
            return {
                'id': self.id,
                'username': str(self.username) if self.username else '',
                'email': str(self.email) if self.email else '',
                'error': f'Serialization error: {str(e)}'
            }