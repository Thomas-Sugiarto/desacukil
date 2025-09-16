from wtforms.validators import ValidationError
from app.models.user import User
import re

class UniqueSlug:
    """Validator untuk memastikan slug unik"""
    def __init__(self, model, field='slug', message=None):
        self.model = model
        self.field = field
        if not message:
            message = f'{field} sudah digunakan.'
        self.message = message

    def __call__(self, form, field):
        existing = self.model.query.filter(
            getattr(self.model, self.field) == field.data
        ).first()
        if existing and (not hasattr(form, '_obj') or not form._obj or existing.id != form._obj.id):
            raise ValidationError(self.message)

class UniqueUsername:
    """Validator untuk memastikan username unik"""
    def __init__(self, message=None):
        if not message:
            message = 'Username sudah digunakan.'
        self.message = message

    def __call__(self, form, field):
        existing = User.query.filter_by(username=field.data).first()
        # Check if this is an edit form and if the existing user is the same as the one being edited
        if existing:
            if hasattr(form, '_obj') and form._obj and existing.id == form._obj.id:
                # This is the same user being edited, allow it
                return
            else:
                # Different user has this username
                raise ValidationError(self.message)

class UniqueEmail:
    """Validator untuk memastikan email unik"""
    def __init__(self, message=None):
        if not message:
            message = 'Email sudah digunakan.'
        self.message = message

    def __call__(self, form, field):
        existing = User.query.filter_by(email=field.data).first()
        # Check if this is an edit form and if the existing user is the same as the one being edited
        if existing:
            if hasattr(form, '_obj') and form._obj and existing.id == form._obj.id:
                # This is the same user being edited, allow it
                return
            else:
                # Different user has this email
                raise ValidationError(self.message)

class YouTubeURL:
    """Validator untuk URL YouTube"""
    def __init__(self, message=None):
        if not message:
            message = 'URL YouTube tidak valid.'
        self.message = message

    def __call__(self, form, field):
        if field.data:
            youtube_regex = re.compile(
                r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
                r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
            )
            if not youtube_regex.match(field.data):
                raise ValidationError(self.message)

class OptionalYouTubeURL:
    """Validator untuk URL YouTube yang optional"""
    def __init__(self, message=None):
        if not message:
            message = 'URL YouTube tidak valid.'
        self.message = message

    def __call__(self, form, field):
        if field.data and field.data.strip():
            youtube_regex = re.compile(
                r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
                r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
            )
            if not youtube_regex.match(field.data.strip()):
                raise ValidationError(self.message)

class StrongPassword:
    """Validator untuk password yang kuat"""
    def __init__(self, message=None):
        if not message:
            message = 'Password harus minimal 8 karakter dengan kombinasi huruf, angka, dan simbol.'
        self.message = message

    def __call__(self, form, field):
        if not field.data:  # Skip validation if password is empty (for edit forms)
            return
            
        password = field.data
        if len(password) < 8:
            raise ValidationError('Password harus minimal 8 karakter.')
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password harus mengandung huruf besar.')
        
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password harus mengandung huruf kecil.')
        
        if not re.search(r'\d', password):
            raise ValidationError('Password harus mengandung angka.')

class PhoneNumber:
    """Validator untuk nomor telepon Indonesia"""
    def __init__(self, message=None):
        if not message:
            message = 'Format nomor telepon tidak valid.'
        self.message = message
    
    def __call__(self, form, field):
        if not field.data:
            return  # Optional field
        
        # Indonesian phone number pattern
        phone_regex = re.compile(r'^(\+62|62|0)[2-9][0-9]{7,11}$')
        
        if not phone_regex.match(field.data.replace('-', '').replace(' ', '')):
            raise ValidationError(self.message)