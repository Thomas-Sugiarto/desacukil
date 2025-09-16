"""
Test configuration and fixtures for CMS Desa
"""

import pytest
import tempfile
import os
from app import create_app, db
from app.models.user import User, Role
from app.models.content import Content, Category
from app.models.setting import Setting

@pytest.fixture
def app():
    """Create application for testing"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        
        # Create test roles
        admin_role = Role(
            name='admin',
            description='Administrator',
            permissions={
                "users": ["create", "read", "update", "delete"],
                "content": ["create", "read", "update", "delete", "publish"],
                "settings": ["read", "update"]
            }
        )
        editor_role = Role(
            name='editor',
            description='Editor',
            permissions={
                "content": ["create", "read", "update", "delete", "review", "publish"]
            }
        )
        publisher_role = Role(
            name='publisher',
            description='Publisher',
            permissions={
                "content": ["create", "read", "update"]
            }
        )
        public_role = Role(
            name='public',
            description='Public',
            permissions={
                "content": ["read"]
            }
        )
        
        db.session.add_all([admin_role, editor_role, publisher_role, public_role])
        db.session.commit()
        
        # Create test category
        test_category = Category(
            name='Test Category',
            slug='test-category',
            description='Test category for testing',
            color='#007bff'
        )
        db.session.add(test_category)
        db.session.commit()
        
        yield app
        
        # Cleanup
        db.session.remove()
        db.drop_all()
        os.close(db_fd)
        os.unlink(db_path)

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()

@pytest.fixture
def admin_user(app):
    """Create admin user for testing"""
    with app.app_context():
        admin_role = Role.query.filter_by(name='admin').first()
        user = User(
            username='admin_test',
            email='admin@test.com',
            full_name='Admin Test',
            role_id=admin_role.id
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def editor_user(app):
    """Create editor user for testing"""
    with app.app_context():
        editor_role = Role.query.filter_by(name='editor').first()
        user = User(
            username='editor_test',
            email='editor@test.com',
            full_name='Editor Test',
            role_id=editor_role.id
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def publisher_user(app):
    """Create publisher user for testing"""
    with app.app_context():
        publisher_role = Role.query.filter_by(name='publisher').first()
        user = User(
            username='publisher_test',
            email='publisher@test.com',
            full_name='Publisher Test',
            role_id=publisher_role.id
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_content(app, publisher_user):
    """Create test content"""
    with app.app_context():
        category = Category.query.filter_by(slug='test-category').first()
        content = Content(
            title='Test Content',
            slug='test-content',
            content='This is test content for testing purposes.',
            excerpt='Test excerpt',
            author_id=publisher_user.id,
            category_id=category.id,
            status='draft'
        )
        db.session.add(content)
        db.session.commit()
        return content

@pytest.fixture
def published_content(app, publisher_user, editor_user):
    """Create published content"""
    with app.app_context():
        category = Category.query.filter_by(slug='test-category').first()
        content = Content(
            title='Published Content',
            slug='published-content',
            content='This is published content for testing.',
            excerpt='Published excerpt',
            author_id=publisher_user.id,
            category_id=category.id,
            reviewer_id=editor_user.id,
            status='published'
        )
        db.session.add(content)
        db.session.commit()
        return content

def login_user(client, username, password):
    """Helper function to login user"""
    return client.post('/auth/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def logout_user(client):
    """Helper function to logout user"""
    return client.get('/auth/logout', follow_redirects=True)

class AuthActions:
    """Helper class for authentication actions"""
    
    def __init__(self, client):
        self._client = client
    
    def login(self, username='admin_test', password='password123'):
        return self._client.post('/auth/login', data={
            'username': username,
            'password': password
        })
    
    def logout(self):
        return self._client.get('/auth/logout')

@pytest.fixture
def auth(client):
    """Authentication helper fixture"""
    return AuthActions(client)