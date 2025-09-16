from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from slugify import slugify
from app import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#28a745')
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    content = db.relationship('Content', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
    def to_dict(self):
        """Convert category to dictionary with safe string handling"""
        try:
            from app.core.security import SecurityManager
            return {
                'id': self.id,
                'name': SecurityManager.safe_str(self.name),
                'slug': SecurityManager.safe_str(self.slug),
                'description': SecurityManager.safe_str(self.description),
                'color': SecurityManager.safe_str(self.color) if self.color else '#28a745',
                'is_active': bool(self.is_active),
                'content_count': self.content.filter_by(status='published').count()
            }
        except Exception as e:
            # Fallback dictionary with minimal safe data
            return {
                'id': self.id,
                'name': str(self.name) if self.name else '',
                'slug': str(self.slug) if self.slug else '',
                'error': f'Serialization error: {str(e)}'
            }

class Content(db.Model):
    __tablename__ = 'content'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    content = db.Column(db.Text)
    excerpt = db.Column(db.Text)
    cover_image = db.Column(db.String(255))
    youtube_url = db.Column(db.String(255))
    status = db.Column(db.String(20), default='draft')  # draft, pending_review, published, rejected
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    review_comment = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    content_metadata = db.Column(db.JSON, default={})  # Renamed from 'metadata' to avoid conflict
    view_count = db.Column(db.Integer, default=0)
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    revisions = db.relationship('ContentRevision', backref='content', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Content {self.title}>'
    
    def generate_slug(self):
        """Generate unique slug from current title"""
        if not self.title:
            return 'untitled'
        
        # Use enhanced slug generation with Unicode support
        from app.core.helpers import make_slug
        base_slug = make_slug(self.title)
        
        if not base_slug:
            base_slug = 'untitled'
        
        slug = base_slug
        counter = 1
        
        # Check for existing slugs, excluding current content if updating
        while True:
            query = Content.query.filter_by(slug=slug)
            if hasattr(self, 'id') and self.id:
                query = query.filter(Content.id != self.id)
            
            if not query.first():
                break
            
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    @staticmethod
    def generate_slug_from_title(title):
        """Static method to generate unique slug from title"""
        if not title:
            return 'untitled'
        
        # Use enhanced slug generation with Unicode support
        from app.core.helpers import make_slug
        base_slug = make_slug(title)
        
        if not base_slug:
            base_slug = 'untitled'
        
        slug = base_slug
        counter = 1
        
        while Content.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def can_edit(self, user):
        """Check if user can edit this content"""
        if user.is_admin() or user.is_editor():
            return True
        return user.id == self.author_id and self.status in ['draft', 'rejected']
    
    def can_delete(self, user):
        """Check if user can delete this content"""
        if user.is_admin():
            return True
        if user.is_editor():
            return True
        return user.id == self.author_id and self.status == 'draft'
    
    def submit_for_review(self):
        """Submit content for review"""
        if self.status == 'draft':
            self.status = 'pending_review'
            return True
        return False
    
    def approve(self, reviewer):
        """Approve content for publishing"""
        if self.status == 'pending_review':
            self.status = 'published'
            self.reviewer_id = reviewer.id
            self.published_at = datetime.utcnow()
            return True
        return False
    
    def reject(self, reviewer, comment):
        """Reject content"""
        if self.status == 'pending_review':
            self.status = 'rejected'
            self.reviewer_id = reviewer.id
            self.review_comment = comment
            return True
        return False
    
    def get_youtube_embed_id(self):
        """Extract YouTube video ID for embedding"""
        if not self.youtube_url:
            return None
        
        import re
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        match = youtube_regex.match(self.youtube_url)
        return match.group(6) if match else None
    
    def to_dict(self):
        """Convert content to dictionary with safe string handling"""
        try:
            from app.core.security import SecurityManager
            return {
                'id': self.id,
                'title': SecurityManager.safe_str(self.title),
                'slug': SecurityManager.safe_str(self.slug),
                'content': SecurityManager.safe_str(self.content),
                'excerpt': SecurityManager.safe_str(self.excerpt),
                'cover_image': SecurityManager.safe_str(self.cover_image),
                'youtube_url': SecurityManager.safe_str(self.youtube_url),
                'status': SecurityManager.safe_str(self.status),
                'author': SecurityManager.safe_str(self.author.full_name) if self.author else '',
                'category': SecurityManager.safe_str(self.category.name) if self.category else '',
                'view_count': int(self.view_count) if self.view_count else 0,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'published_at': self.published_at.isoformat() if self.published_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
                'review_comment': SecurityManager.safe_str(self.review_comment)
            }
        except Exception as e:
            # Fallback dictionary with minimal safe data
            return {
                'id': self.id,
                'title': str(self.title) if self.title else '',
                'status': str(self.status) if self.status else 'draft',
                'error': f'Serialization error: {str(e)}'
            }

class ContentRevision(db.Model):
    __tablename__ = 'content_revisions'
    
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'), nullable=False)
    title_snapshot = db.Column(db.String(255))
    content_snapshot = db.Column(db.Text)
    revised_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    revision_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviser = db.relationship('User', backref='content_revisions')
    
    def __repr__(self):
        return f'<ContentRevision {self.id}>'
    
    def to_dict(self):
        """Convert revision to dictionary with safe string handling"""
        try:
            from app.core.security import SecurityManager
            return {
                'id': self.id,
                'content_id': self.content_id,
                'title_snapshot': SecurityManager.safe_str(self.title_snapshot),
                'content_snapshot': SecurityManager.safe_str(self.content_snapshot),
                'revision_notes': SecurityManager.safe_str(self.revision_notes),
                'revised_by': SecurityManager.safe_str(self.reviser.full_name) if self.reviser else '',
                'created_at': self.created_at.isoformat() if self.created_at else None
            }
        except Exception as e:
            # Fallback dictionary with minimal safe data
            return {
                'id': self.id,
                'content_id': self.content_id,
                'error': f'Serialization error: {str(e)}'
            }