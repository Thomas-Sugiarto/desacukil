from flask import request, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import re
from urllib.parse import urlparse, urljoin
import bleach

class SecurityManager:
    
    @staticmethod
    def hash_password(password):
        """Hash password menggunakan werkzeug"""
        return generate_password_hash(password, method='pbkdf2:sha256')
    
    @staticmethod
    def check_password(password_hash, password):
        """Verifikasi password"""
        return check_password_hash(password_hash, password)
    
    @staticmethod
    def generate_csrf_token():
        """Generate CSRF token"""
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_urlsafe(32)
        return session['_csrf_token']
    
    @staticmethod
    def validate_csrf_token(token):
        """Validasi CSRF token"""
        return token == session.get('_csrf_token')
    
    @staticmethod
    def sanitize_html(content):
        """Sanitasi HTML untuk mencegah XSS"""
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                       'ul', 'ol', 'li', 'a', 'img', 'blockquote', 'code', 'pre', 'div', 'span']
        allowed_attributes = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'width', 'height', 'class'],
            'div': ['class'],
            'span': ['class'],
        }
        return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes)
    
    @staticmethod
    def validate_youtube_url(url):
        """Validasi URL YouTube"""
        if not url:
            return True  # Optional field
        
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return youtube_regex.match(url) is not None
    
    @staticmethod
    def extract_youtube_id(url):
        """Extract YouTube video ID from various YouTube URL formats"""
        if not url:
            return None
        
        # Multiple regex patterns to handle different YouTube URL formats
        patterns = [
            # Standard watch URL: https://www.youtube.com/watch?v=VIDEO_ID
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&=%\?]{11})',
            # Short URL: https://youtu.be/VIDEO_ID
            r'(?:https?://)?youtu\.be/([^&=%\?]{11})',
            # Embed URL: https://www.youtube.com/embed/VIDEO_ID
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^&=%\?]{11})',
            # YouTube nocookie: https://www.youtube-nocookie.com/embed/VIDEO_ID
            r'(?:https?://)?(?:www\.)?youtube-nocookie\.com/embed/([^&=%\?]{11})',
            # Mobile URL: https://m.youtube.com/watch?v=VIDEO_ID
            r'(?:https?://)?m\.youtube\.com/watch\?v=([^&=%\?]{11})',
            # URL with additional parameters: https://www.youtube.com/watch?v=VIDEO_ID&t=123s
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v=([^&=%\?]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def is_safe_url(target):
        """Check if URL is safe for redirect"""
        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    
    @staticmethod
    def secure_filename(filename):
        """Make filename secure - Python 3 compatible version"""
        import unicodedata
        import string
        
        # Ensure we have a string
        if not isinstance(filename, str):
            filename = str(filename)
        
        # Normalize unicode characters to remove accents and special chars
        filename = unicodedata.normalize('NFKD', filename)
        
        # Convert to ASCII, ignoring non-ASCII characters
        # This is Python 3 compatible and handles unicode properly
        try:
            filename = filename.encode('ascii', 'ignore').decode('ascii')
        except (UnicodeDecodeError, UnicodeEncodeError):
            # Fallback: keep only ASCII characters
            filename = ''.join(c for c in filename if ord(c) < 128)
        
        # Keep only alphanumeric characters, dots, hyphens and underscores
        valid_chars = "-_.() " + string.ascii_letters + string.digits
        filename = ''.join(c for c in filename if c in valid_chars)
        
        # Replace spaces with underscores and clean up
        filename = filename.replace(' ', '_')
        
        # Remove multiple consecutive underscores
        filename = re.sub(r'_+', '_', filename)
        
        # Remove leading/trailing underscores and dots
        filename = filename.strip('_.')
        
        # Ensure filename is not empty
        if not filename:
            filename = 'unnamed_file'
        
        return filename
    
    @staticmethod
    def safe_str(obj):
        """Safely convert any object to string - Python 3 compatible"""
        if obj is None:
            return ''
        
        if isinstance(obj, str):
            return obj
        
        if isinstance(obj, bytes):
            try:
                return obj.decode('utf-8', errors='ignore')
            except (UnicodeDecodeError, AttributeError):
                return str(obj)
        
        # For other types (int, float, datetime, etc.)
        try:
            return str(obj)
        except (UnicodeDecodeError, UnicodeEncodeError):
            # Fallback for problematic objects
            return repr(obj)