# System Design Document
# CMS Desa - Sistem Manajemen Konten Desa Berbasis Flask

## Implementation Approach

Berdasarkan analisis PRD, sistem CMS Desa memerlukan arsitektur yang robust dengan fokus pada keamanan, scalability, dan user experience. Pendekatan implementasi yang dipilih:

### Difficult Points Analysis
1. **Multi-Role Workflow Management**: Implementasi state machine untuk content workflow dengan role-based permissions
2. **Security Implementation**: CSRF protection, XSS prevention, dan role-based access control
3. **Media Management**: Upload handling dengan validasi dan YouTube embed integration
4. **Production Deployment**: Konfigurasi untuk PostgreSQL, Gunicorn, dan Nginx

### Selected Open-Source Framework
- **Flask 2.3+**: Lightweight, flexible, dengan ecosystem yang mature
- **SQLAlchemy**: ORM dengan support untuk complex relationships dan migrations
- **Flask-Login**: Session management dan user authentication
- **Flask-WTF**: Form handling dengan CSRF protection
- **Flask-Migrate**: Database migration management
- **Bootstrap 5**: Responsive UI framework
- **PostgreSQL**: Production-grade database dengan ACID compliance

### Architecture Pattern
- **Blueprint-based Modular Architecture**: Separation of concerns berdasarkan user roles
- **MVC Pattern**: Model-View-Controller untuk maintainability
- **Repository Pattern**: Data access layer abstraction
- **Service Layer Pattern**: Business logic separation

## Data Structures and Interfaces

### Database Schema Design

#### Core Tables Structure
```sql
-- Roles table (Master data)
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content status enum
CREATE TYPE content_status AS ENUM ('draft', 'pending_review', 'published', 'rejected');

-- Content categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main content table
CREATE TABLE content (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL,
    cover_image VARCHAR(255),
    youtube_url VARCHAR(255),
    status content_status DEFAULT 'draft',
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    reviewer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    review_comment TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content workflow history
CREATE TABLE content_workflow (
    id SERIAL PRIMARY KEY,
    content_id INTEGER NOT NULL REFERENCES content(id) ON DELETE CASCADE,
    from_status content_status,
    to_status content_status NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System settings
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_content_status ON content(status);
CREATE INDEX idx_content_author ON content(author_id);
CREATE INDEX idx_content_published ON content(published_at);
CREATE INDEX idx_content_slug ON content(slug);
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_workflow_content ON content_workflow(content_id);
```

### Flask Application Structure

```
cms_desa/
├── app/
│   ├── __init__.py                 # Application factory
│   ├── config.py                   # Configuration classes
│   ├── extensions.py               # Flask extensions initialization
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                 # User and Role models
│   │   ├── content.py              # Content and Category models
│   │   ├── workflow.py             # Workflow tracking
│   │   └── settings.py             # System settings
│   ├── blueprints/
│   │   ├── __init__.py
│   │   ├── auth/                   # Authentication blueprint
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── forms.py
│   │   │   └── templates/
│   │   ├── admin/                  # Admin management
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── forms.py
│   │   │   └── templates/
│   │   ├── editor/                 # Editor workflow
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── forms.py
│   │   │   └── templates/
│   │   ├── publisher/              # Publisher content creation
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   ├── forms.py
│   │   │   └── templates/
│   │   └── public/                 # Public website
│   │       ├── __init__.py
│   │       ├── routes.py
│   │       └── templates/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py         # Authentication business logic
│   │   ├── content_service.py      # Content management logic
│   │   ├── workflow_service.py     # Workflow management
│   │   ├── media_service.py        # File upload handling
│   │   └── notification_service.py # Email notifications
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── decorators.py           # Custom decorators
│   │   ├── validators.py           # Input validation
│   │   ├── helpers.py              # Utility functions
│   │   └── security.py             # Security utilities
│   ├── static/
│   │   ├── css/
│   │   │   ├── bootstrap.min.css
│   │   │   ├── admin.css
│   │   │   └── public.css
│   │   ├── js/
│   │   │   ├── bootstrap.bundle.min.js
│   │   │   ├── admin.js
│   │   │   └── public.js
│   │   ├── images/
│   │   └── uploads/                # User uploaded files
│   └── templates/
│       ├── base/
│       │   ├── admin_base.html
│       │   ├── public_base.html
│       │   └── auth_base.html
│       ├── components/
│       │   ├── navbar.html
│       │   ├── sidebar.html
│       │   └── pagination.html
│       └── errors/
│           ├── 404.html
│           ├── 403.html
│           └── 500.html
├── migrations/                     # Database migrations
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_content.py
│   ├── test_workflow.py
│   └── conftest.py
├── deployment/
│   ├── nginx.conf
│   ├── gunicorn.conf.py
│   ├── supervisor.conf
│   └── docker/
│       ├── Dockerfile
│       └── docker-compose.yml
├── scripts/
│   ├── seed_data.py                # Database seeding
│   ├── backup.py                   # Backup utilities
│   └── deploy.py                   # Deployment script
├── .env.example                    # Environment variables template
├── .gitignore
├── config.py                       # Configuration management
├── requirements.txt
├── run.py                          # Application entry point
└── README.md
```

## Program Call Flow

### Content Publishing Workflow

```mermaid
sequenceDiagram
    participant P as Publisher
    participant PS as PublisherService
    participant CS as ContentService
    participant WS as WorkflowService
    participant DB as Database
    participant E as Editor
    participant ES as EditorService
    participant NS as NotificationService

    Note over P,NS: Content Creation Flow
    P->>PS: create_content(title, content, media)
    PS->>CS: validate_content_data(data)
    CS->>CS: generate_slug(title)
    CS->>CS: validate_youtube_url(url)
    CS->>DB: save_content(status='draft')
    DB-->>CS: content_id
    CS->>WS: log_workflow(content_id, 'draft', user_id)
    WS->>DB: insert_workflow_history
    CS-->>PS: content_created
    PS-->>P: redirect_to_content_list

    Note over P,NS: Submit for Review
    P->>PS: submit_for_review(content_id)
    PS->>CS: update_content_status(content_id, 'pending_review')
    CS->>DB: update_content_status
    CS->>WS: log_workflow(content_id, 'draft->pending_review')
    WS->>NS: notify_editors(content_id)
    NS->>NS: send_email_notification
    CS-->>PS: status_updated
    PS-->>P: show_success_message

    Note over E,NS: Editor Review Process
    E->>ES: review_content(content_id)
    ES->>CS: get_content_with_author(content_id)
    CS->>DB: fetch_content_details
    DB-->>CS: content_data
    CS-->>ES: content_details
    ES-->>E: show_review_interface

    alt Editor Approves
        E->>ES: approve_content(content_id, comment)
        ES->>CS: update_content_status(content_id, 'published')
        CS->>DB: update_content(status='published', published_at=now())
        CS->>WS: log_workflow(content_id, 'pending_review->published')
        WS->>NS: notify_author(content_id, 'approved')
    else Editor Rejects
        E->>ES: reject_content(content_id, comment)
        ES->>CS: update_content_status(content_id, 'rejected')
        CS->>DB: update_content(status='rejected', review_comment)
        CS->>WS: log_workflow(content_id, 'pending_review->rejected')
        WS->>NS: notify_author(content_id, 'rejected')
    end
```

### User Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant AS as AuthService
    participant DB as Database
    participant S as Session
    participant R as RoleService

    Note over U,R: Login Process
    U->>AS: login(username, password)
    AS->>AS: validate_input(username, password)
    AS->>DB: get_user_by_username(username)
    DB-->>AS: user_data
    AS->>AS: verify_password(password, user.password_hash)
    
    alt Valid Credentials
        AS->>S: create_session(user_id)
        AS->>R: get_user_permissions(user.role_id)
        R->>DB: fetch_role_permissions(role_id)
        DB-->>R: permissions_data
        R-->>AS: user_permissions
        AS->>S: store_permissions(permissions)
        AS-->>U: redirect_to_dashboard
    else Invalid Credentials
        AS-->>U: show_error_message
    end

    Note over U,R: Access Control Check
    U->>AS: access_protected_route()
    AS->>S: check_session_valid()
    S-->>AS: session_status
    
    alt Valid Session
        AS->>R: check_permission(required_permission)
        R->>S: get_user_permissions()
        S-->>R: user_permissions
        R->>R: validate_permission(required_permission, user_permissions)
        
        alt Has Permission
            R-->>AS: access_granted
            AS-->>U: serve_content
        else No Permission
            R-->>AS: access_denied
            AS-->>U: redirect_to_403
        end
    else Invalid Session
        AS-->>U: redirect_to_login
    end
```

### Admin User Management Flow

```mermaid
sequenceDiagram
    participant A as Admin
    participant AS as AdminService
    participant US as UserService
    participant RS as RoleService
    participant DB as Database
    participant VS as ValidationService

    Note over A,VS: Create User Process
    A->>AS: create_user(user_data)
    AS->>VS: validate_user_data(user_data)
    VS->>VS: check_username_unique(username)
    VS->>VS: check_email_unique(email)
    VS->>VS: validate_password_strength(password)
    VS-->>AS: validation_result
    
    alt Validation Passed
        AS->>US: hash_password(password)
        US->>US: generate_password_hash(password)
        US->>DB: create_user(hashed_data)
        DB-->>US: user_id
        US->>RS: assign_role(user_id, role_id)
        RS->>DB: update_user_role(user_id, role_id)
        US-->>AS: user_created
        AS-->>A: show_success_message
    else Validation Failed
        AS-->>A: show_validation_errors
    end

    Note over A,VS: Role Management
    A->>AS: manage_roles()
    AS->>RS: get_all_roles()
    RS->>DB: fetch_roles_with_permissions()
    DB-->>RS: roles_data
    RS-->>AS: roles_list
    AS-->>A: display_roles_interface

    A->>AS: update_role_permissions(role_id, permissions)
    AS->>RS: validate_permissions(permissions)
    RS->>RS: check_permission_format(permissions)
    RS->>DB: update_role_permissions(role_id, permissions)
    DB-->>RS: update_result
    RS-->>AS: permissions_updated
    AS-->>A: show_success_message
```

## API Endpoints and Routing

### Authentication Routes (`/auth`)
```python
# Authentication Blueprint Routes
POST   /auth/login              # User login
POST   /auth/logout             # User logout
GET    /auth/profile            # User profile view
POST   /auth/profile            # Update user profile
POST   /auth/change-password    # Change password
```

### Admin Routes (`/admin`)
```python
# Admin Management Routes
GET    /admin/dashboard         # Admin dashboard
GET    /admin/users             # List all users
POST   /admin/users             # Create new user
GET    /admin/users/<id>        # View user details
PUT    /admin/users/<id>        # Update user
DELETE /admin/users/<id>        # Delete user
GET    /admin/roles             # Manage roles
POST   /admin/roles             # Create/update role
GET    /admin/settings          # System settings
POST   /admin/settings          # Update settings
GET    /admin/content           # All content management
POST   /admin/content/<id>/status  # Force status change
```

### Editor Routes (`/editor`)
```python
# Editor Workflow Routes
GET    /editor/dashboard        # Editor dashboard
GET    /editor/pending          # Pending review content
GET    /editor/content          # All content (published/rejected)
GET    /editor/content/<id>     # View content details
POST   /editor/content/<id>/approve    # Approve content
POST   /editor/content/<id>/reject     # Reject content
GET    /editor/content/<id>/edit       # Edit content
POST   /editor/content/<id>/edit       # Update content
POST   /editor/content/create          # Create new content (editor privilege)
```

### Publisher Routes (`/publisher`)
```python
# Publisher Content Routes
GET    /publisher/dashboard     # Publisher dashboard
GET    /publisher/content       # My content list
GET    /publisher/content/create # Create content form
POST   /publisher/content/create # Submit new content
GET    /publisher/content/<id>/edit    # Edit draft content
POST   /publisher/content/<id>/edit    # Update draft content
POST   /publisher/content/<id>/submit  # Submit for review
DELETE /publisher/content/<id>         # Delete draft content
```

### Public Routes (`/`)
```python
# Public Website Routes
GET    /                        # Homepage
GET    /berita                  # News listing
GET    /berita/<slug>           # News detail
GET    /kegiatan                # Activities listing
GET    /kegiatan/<slug>         # Activity detail
GET    /pengumuman              # Announcements
GET    /pengumuman/<slug>       # Announcement detail
GET    /profil-desa             # Village profile
GET    /kontak                  # Contact information
GET    /search                  # Search results
GET    /kategori/<slug>         # Category listing
```

### API Routes (`/api/v1`)
```python
# REST API for future mobile app
GET    /api/v1/content          # List published content
GET    /api/v1/content/<id>     # Get content by ID
GET    /api/v1/categories       # List categories
POST   /api/v1/upload           # File upload endpoint
GET    /api/v1/settings/public  # Public settings
```

## Security Layer and Middleware

### Authentication & Authorization Middleware

```python
# Role-based access control decorator
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if current_user.role.name not in roles:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Permission-based access control
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### Input Validation & Sanitization

```python
# Custom validators
class ContentValidator:
    @staticmethod
    def validate_title(title):
        if len(title) < 5 or len(title) > 255:
            raise ValidationError('Title must be 5-255 characters')
        return bleach.clean(title)
    
    @staticmethod
    def validate_slug(slug):
        if not re.match(r'^[a-z0-9-]+$', slug):
            raise ValidationError('Invalid slug format')
        return slug
    
    @staticmethod
    def validate_youtube_url(url):
        youtube_pattern = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        if url and not re.match(youtube_pattern, url):
            raise ValidationError('Invalid YouTube URL')
        return url

# XSS Prevention
def sanitize_html_content(content):
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                   'ul', 'ol', 'li', 'blockquote', 'a', 'img']
    allowed_attributes = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height']
    }
    return bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes)
```

### CSRF Protection Configuration

```python
# CSRF configuration in app/__init__.py
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    csrf.init_app(app)
    
    # CSRF error handler
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/csrf_error.html', 
                             reason=e.description), 400
```

### File Upload Security

```python
# Secure file upload handling
class MediaService:
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    @staticmethod
    def allowed_file(filename):
        return ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in MediaService.ALLOWED_EXTENSIONS)
    
    @staticmethod
    def secure_upload(file):
        if file and MediaService.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Validate file size
            file.seek(0, os.SEEK_END)
            if file.tell() > MediaService.MAX_FILE_SIZE:
                raise ValidationError('File too large')
            file.seek(0)
            
            # Save file
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(upload_path)
            
            return unique_filename
        raise ValidationError('Invalid file type')
```

## Deployment Architecture for Production

### Server Configuration

```nginx
# /etc/nginx/sites-available/cms_desa
server {
    listen 80;
    server_name cms-desa.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cms-desa.example.com;
    
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Static files
    location /static {
        alias /var/www/cms_desa/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media uploads
    location /uploads {
        alias /var/www/cms_desa/app/static/uploads;
        expires 1M;
    }
    
    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # File upload size limit
    client_max_body_size 10M;
}
```

### Gunicorn Configuration

```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 2

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = "/var/log/cms_desa/access.log"
errorlog = "/var/log/cms_desa/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "cms_desa"

# Preload application
preload_app = True

# Worker recycling
max_requests = 1000
max_requests_jitter = 50
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP=run.py

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create uploads directory
RUN mkdir -p app/static/uploads

# Collect static files and set permissions
RUN chmod +x scripts/deploy.py

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://cms_user:cms_password@db:5432/cms_desa
    depends_on:
      - db
      - redis
    volumes:
      - ./app/static/uploads:/app/app/static/uploads
      - ./logs:/app/logs

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=cms_desa
      - POSTGRES_USER=cms_user
      - POSTGRES_PASSWORD=cms_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backup:/backup
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/ssl/certs
      - ./app/static:/var/www/static
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
```

### Environment Configuration

```python
# config.py
import os
from datetime import timedelta

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://cms_user:cms_password@localhost/cms_desa'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 7200,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    # Security
    WTF_CSRF_TIME_LIMIT = 3600
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app/static/uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Application settings
    POSTS_PER_PAGE = 10
    LANGUAGES = ['id']
    
class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    
    # Enhanced security for production
    PREFERRED_URL_SCHEME = 'https'
    SESSION_COOKIE_SECURE = True
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/cms_desa/app.log'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

### Database Backup Strategy

```python
# scripts/backup.py
import os
import subprocess
import datetime
from pathlib import Path

class DatabaseBackup:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.backup_dir = Path('/backup')
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self):
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'cms_desa_backup_{timestamp}.sql'
        
        cmd = [
            'pg_dump',
            self.db_url,
            '-f', str(backup_file),
            '--verbose',
            '--clean',
            '--no-owner',
            '--no-privileges'
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Backup created successfully: {backup_file}")
            
            # Cleanup old backups (keep last 7 days)
            self.cleanup_old_backups()
            
        except subprocess.CalledProcessError as e:
            print(f"Backup failed: {e}")
    
    def cleanup_old_backups(self):
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=7)
        
        for backup_file in self.backup_dir.glob('cms_desa_backup_*.sql'):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                backup_file.unlink()
                print(f"Deleted old backup: {backup_file}")

if __name__ == '__main__':
    backup = DatabaseBackup()
    backup.create_backup()
```

## Anything UNCLEAR

1. **Content Categories**: PRD menyebutkan navigasi seperti "berita/kegiatan" tapi tidak spesifik tentang sistem kategorisasi. Apakah diperlukan kategori yang dapat dikonfigurasi atau fixed categories?

2. **File Storage Location**: Untuk production, apakah menggunakan local storage atau cloud storage (AWS S3, Google Cloud Storage) untuk media files? Local storage lebih sederhana tapi cloud storage lebih scalable.

3. **Email Notification System**: Workflow approval memerlukan notifikasi, tapi belum jelas SMTP server mana yang akan digunakan dan format email template yang diinginkan.

4. **Content Versioning**: Apakah diperlukan versioning untuk content yang sudah di-edit? Ini penting untuk audit trail tapi menambah kompleksitas database.

5. **Performance Requirements**: Berapa concurrent users yang harus didukung? Ini mempengaruhi konfigurasi server dan database connection pooling.

6. **Backup & Recovery**: Strategi backup untuk media files belum jelas. Apakah cukup database backup atau perlu backup file system juga?

7. **Mobile Responsiveness**: PRD menyebutkan Bootstrap 5 tapi tidak spesifik tentang breakpoints dan mobile-first approach yang diinginkan.

8. **SEO Requirements**: Apakah diperlukan SEO optimization seperti meta tags, sitemap generation, dan structured data markup?

9. **Analytics Integration**: Apakah diperlukan integrasi dengan Google Analytics atau sistem analytics lainnya untuk tracking visitor behavior?

10. **Content Scheduling**: Apakah diperlukan fitur untuk schedule publish content di waktu tertentu?