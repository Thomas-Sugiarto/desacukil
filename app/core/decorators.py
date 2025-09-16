from functools import wraps
from flask import abort, request, redirect, url_for, flash
from flask_login import current_user

def role_required(*roles):
    """Decorator untuk mengecek role user"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if current_user.role.name not in roles:
                flash('Anda tidak memiliki akses ke halaman ini.', 'error')
                return abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(resource, action):
    """Decorator untuk mengecek permission spesifik"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if not current_user.has_permission(resource, action):
                flash('Anda tidak memiliki permission untuk aksi ini.', 'error')
                return abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator untuk admin only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('Akses ditolak. Hanya admin yang dapat mengakses halaman ini.', 'error')
            return abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def editor_required(f):
    """Decorator untuk editor dan admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_editor():
            flash('Akses ditolak. Hanya editor dan admin yang dapat mengakses halaman ini.', 'error')
            return abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def publisher_required(f):
    """Decorator untuk publisher, editor, dan admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_publisher():
            flash('Akses ditolak. Anda tidak memiliki akses ke halaman ini.', 'error')
            return abort(403)
        
        return f(*args, **kwargs)
    return decorated_function