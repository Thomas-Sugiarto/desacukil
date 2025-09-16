from flask import current_app, request, url_for
from werkzeug.utils import secure_filename
import os
import re
import unicodedata
from datetime import datetime, timedelta
import hashlib
import secrets
import json

class MomentJS:
    """A simple moment.js-like class for template use"""
    def __init__(self, dt=None):
        self.dt = dt or datetime.now()
    
    def format(self, format_str):
        """Format datetime with Indonesian month names"""
        # Indonesian month names
        months = {
            1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
            5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
        }
        
        if format_str == 'DD MMMM YYYY':
            return f"{self.dt.day:02d} {months[self.dt.month]} {self.dt.year}"
        elif format_str == 'DD MMM YYYY':
            return f"{self.dt.day:02d} {months[self.dt.month][:3]} {self.dt.year}"
        elif format_str == 'YYYY-MM-DD':
            return self.dt.strftime('%Y-%m-%d')
        elif format_str == 'DD/MM/YYYY':
            return self.dt.strftime('%d/%m/%Y')
        else:
            # Fallback to standard strftime
            return self.dt.strftime(format_str)
    
    def subtract(self, amount, unit):
        """Subtract time from current datetime"""
        if unit == 'day' or unit == 'days':
            new_dt = self.dt - timedelta(days=amount)
        elif unit == 'hour' or unit == 'hours':
            new_dt = self.dt - timedelta(hours=amount)
        elif unit == 'minute' or unit == 'minutes':
            new_dt = self.dt - timedelta(minutes=amount)
        elif unit == 'second' or unit == 'seconds':
            new_dt = self.dt - timedelta(seconds=amount)
        else:
            new_dt = self.dt
        
        return MomentJS(new_dt)
    
    def add(self, amount, unit):
        """Add time to current datetime"""
        if unit == 'day' or unit == 'days':
            new_dt = self.dt + timedelta(days=amount)
        elif unit == 'hour' or unit == 'hours':
            new_dt = self.dt + timedelta(hours=amount)
        elif unit == 'minute' or unit == 'minutes':
            new_dt = self.dt + timedelta(minutes=amount)
        elif unit == 'second' or unit == 'seconds':
            new_dt = self.dt + timedelta(seconds=amount)
        else:
            new_dt = self.dt
        
        return MomentJS(new_dt)
    
    def date(self):
        """Return date part only"""
        return self.dt.date()

def register_template_helpers(app):
    """Register template filters and global functions"""
    
    @app.template_global()
    def moment(dt=None):
        """Create a moment-like object for date formatting"""
        return MomentJS(dt)
    
    @app.template_filter('datetime')
    def datetime_filter(dt, format='%d %B %Y'):
        """Format datetime for templates"""
        if dt is None:
            return ""
        
        # Indonesian month names
        months = {
            1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
            5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember'
        }
        
        if format == '%d %B %Y':
            return f"{dt.day} {months[dt.month]} {dt.year}"
        elif format == '%d %b %Y':
            return f"{dt.day} {months[dt.month][:3]} {dt.year}"
        else:
            return dt.strftime(format)
    
    @app.template_filter('timeago')
    def timeago_filter(dt):
        """Show relative time"""
        if dt is None:
            return ""
        
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} hari yang lalu"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} jam yang lalu"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} menit yang lalu"
        else:
            return "Baru saja"
    
    @app.template_filter('truncate_words')
    def truncate_words_filter(text, length=20):
        """Truncate text by words"""
        if not text:
            return ""
        
        words = str(text).split()
        if len(words) <= length:
            return str(text)
        
        return ' '.join(words[:length]) + '...'
    
    @app.template_filter('status_badge')
    def status_badge_filter(status):
        """Return Bootstrap badge class for status"""
        badges = {
            'draft': 'secondary',
            'pending_review': 'warning',
            'published': 'success',
            'rejected': 'danger',
            'active': 'success',
            'inactive': 'secondary'
        }
        return badges.get(str(status), 'secondary')
    
    @app.template_filter('status_text')
    def status_text_filter(status):
        """Return Indonesian text for status"""
        texts = {
            'draft': 'Draft',
            'pending_review': 'Menunggu Review',
            'published': 'Dipublikasi',
            'rejected': 'Ditolak',
            'active': 'Aktif',
            'inactive': 'Tidak Aktif'
        }
        return texts.get(str(status), str(status).title())
    
    @app.template_global()
    def get_youtube_embed_url(youtube_url):
        """Get YouTube embed URL"""
        if not youtube_url:
            return None
        
        from app.core.security import SecurityManager
        video_id = SecurityManager.extract_youtube_id(youtube_url)
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
        return None
    
    @app.template_global()
    def url_for_other_page(page):
        """Generate URL for pagination"""
        from flask import request, url_for
        args = request.view_args.copy()
        args.update(request.args.to_dict())
        args['page'] = page
        return url_for(request.endpoint, **args)
    
    @app.template_global()
    def get_file_url(filename):
        """Get URL for uploaded file"""
        if not filename:
            return None
        return f"/static/uploads/{filename}"

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', set())

def get_file_extension(filename):
    """Get file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def generate_unique_filename(filename):
    """Generate unique filename with timestamp"""
    name, ext = os.path.splitext(secure_filename(filename))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_str = secrets.token_hex(4)
    return f"{name}_{timestamp}_{random_str}{ext}"

def get_file_size_mb(file_path):
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    except OSError:
        return 0

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{round(size_bytes / 1024, 1)} KB"
    elif size_bytes < 1024**3:
        return f"{round(size_bytes / (1024**2), 1)} MB"
    else:
        return f"{round(size_bytes / (1024**3), 1)} GB"

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s-.]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-.')

def create_directory_if_not_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return directory

def get_upload_path(subfolder=''):
    """Get upload path with optional subfolder"""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    if subfolder:
        upload_folder = os.path.join(upload_folder, subfolder)
    return create_directory_if_not_exists(upload_folder)

def generate_hash(text):
    """Generate MD5 hash of text"""
    # Ensure text is properly encoded
    if isinstance(text, str):
        text_bytes = text.encode('utf-8')
    else:
        text_bytes = str(text).encode('utf-8')
    return hashlib.md5(text_bytes).hexdigest()

def truncate_text(text, length=100, suffix='...'):
    """Truncate text to specified length"""
    if not text:
        return ''
    text = str(text)
    if len(text) <= length:
        return text
    return text[:length].rstrip() + suffix

def format_datetime(dt, format_str='%d %B %Y, %H:%M'):
    """Format datetime object"""
    if not dt:
        return ''
    return dt.strftime(format_str)

def time_ago(dt):
    """Get human readable time difference"""
    if not dt:
        return ''
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} hari yang lalu"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} jam yang lalu"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} menit yang lalu"
    else:
        return "Baru saja"

def get_client_ip():
    """Get client IP address"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']

def is_ajax_request():
    """Check if request is AJAX"""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def json_response(data, status_code=200):
    """Create JSON response"""
    from flask import jsonify
    response = jsonify(data)
    response.status_code = status_code
    return response

def error_response(message, status_code=400):
    """Create error response"""
    return json_response({'error': message}, status_code)

def success_response(message, data=None):
    """Create success response"""
    response_data = {'success': True, 'message': message}
    if data:
        response_data['data'] = data
    return json_response(response_data)

def make_slug(text):
    """Create URL-friendly slug from text - Python 3 compatible with enhanced Unicode handling"""
    if not text:
        return ''
    
    # Convert to string if not already
    text = str(text)
    
    # Normalize unicode characters
    try:
        text = unicodedata.normalize('NFKD', text)
    except Exception:
        # If normalization fails, continue with original text
        pass
    
    # Convert to ASCII, ignoring non-ASCII characters
    try:
        text = text.encode('ascii', 'ignore').decode('ascii')
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Fallback: keep only ASCII characters
        text = ''.join(c for c in text if ord(c) < 128)
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Ensure slug is not empty
    if not text:
        text = 'untitled'
    
    return text

def save_uploaded_file(file, folder='covers'):
    """Save uploaded file and return filename with enhanced error handling"""
    if not file:
        return None
    
    try:
        from app.core.security import SecurityManager
        
        if file and SecurityManager.allowed_file(file.filename):
            # Generate unique filename
            import uuid
            
            # Safely get file extension
            try:
                extension = file.filename.rsplit('.', 1)[1].lower()
            except (AttributeError, IndexError):
                extension = 'bin'  # Default extension if none found
            
            filename = str(uuid.uuid4()) + '.' + extension
            
            # Create upload directory if it doesn't exist
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
            os.makedirs(upload_path, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            return f"{folder}/{filename}"
    except Exception as e:
        # Log the error but don't crash the application
        print(f"Error saving file: {str(e)}")
        return None
    
    return None

def delete_uploaded_file(filename):
    """Delete uploaded file with enhanced error handling"""
    if not filename:
        return
    
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # Log the error but don't crash the application
        print(f"Error deleting file {filename}: {str(e)}")

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate Indonesian phone number"""
    if not phone:
        return True  # Optional field
    
    # Remove spaces and hyphens
    phone = re.sub(r'[\s-]', '', phone)
    
    # Indonesian phone number pattern
    pattern = r'^(\+62|62|0)[2-9][0-9]{7,11}$'
    return re.match(pattern, phone) is not None

def format_phone(phone):
    """Format phone number for display"""
    if not phone:
        return ''
    
    # Remove spaces and hyphens
    phone = re.sub(r'[\s-]', '', phone)
    
    # Add country code if not present
    if phone.startswith('0'):
        phone = '+62' + phone[1:]
    elif phone.startswith('62'):
        phone = '+' + phone
    elif not phone.startswith('+62'):
        phone = '+62' + phone
    
    return phone

def generate_password(length=12):
    """Generate random password"""
    import string
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))

def mask_email(email):
    """Mask email for privacy"""
    if not email or '@' not in email:
        return email
    
    username, domain = email.split('@', 1)
    if len(username) <= 2:
        masked_username = username
    else:
        masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
    
    return f"{masked_username}@{domain}"

def get_pagination_info(pagination):
    """Get pagination information"""
    return {
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'has_prev': pagination.has_prev,
        'prev_num': pagination.prev_num,
        'has_next': pagination.has_next,
        'next_num': pagination.next_num,
        'items': len(pagination.items)
    }

def clean_html(html_content):
    """Clean HTML content"""
    if not html_content:
        return ''
    
    html_content = str(html_content)
    
    # Remove script and style tags
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags but keep content
    html_content = re.sub(r'<[^>]+>', '', html_content)
    
    # Clean up whitespace
    html_content = re.sub(r'\s+', ' ', html_content).strip()
    
    return html_content

def extract_text_from_html(html_content, max_length=None):
    """Extract plain text from HTML"""
    text = clean_html(html_content)
    if max_length and len(text) > max_length:
        text = truncate_text(text, max_length)
    return text

def get_file_icon(filename):
    """Get icon class for file type"""
    if not filename:
        return 'bi-file'
    
    ext = get_file_extension(filename)
    
    icon_map = {
        'pdf': 'bi-file-pdf',
        'doc': 'bi-file-word',
        'docx': 'bi-file-word',
        'xls': 'bi-file-excel',
        'xlsx': 'bi-file-excel',
        'ppt': 'bi-file-ppt',
        'pptx': 'bi-file-ppt',
        'jpg': 'bi-file-image',
        'jpeg': 'bi-file-image',
        'png': 'bi-file-image',
        'gif': 'bi-file-image',
        'zip': 'bi-file-zip',
        'rar': 'bi-file-zip',
        'txt': 'bi-file-text',
        'csv': 'bi-file-spreadsheet'
    }
    
    return icon_map.get(ext, 'bi-file')

def safe_int(value, default=0):
    """Safely convert value to integer"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def get_env_bool(key, default=False):
    """Get boolean value from environment variable"""
    value = os.environ.get(key, '').lower()
    return value in ('true', '1', 'yes', 'on') if value else default

def safe_str(obj):
    """Safely convert any object to string - Enhanced version"""
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