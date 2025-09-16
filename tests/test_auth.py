"""
Authentication tests for CMS Desa
"""

import pytest
from flask import url_for
from app.models.user import User, Role
from app import db

class TestAuth:
    """Test authentication functionality"""
    
    def test_login_page_loads(self, client):
        """Test login page loads correctly"""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Portal Desa Digital' in response.data
        assert b'Username' in response.data
        assert b'Password' in response.data
    
    def test_valid_login(self, client, admin_user):
        """Test login with valid credentials"""
        response = client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Selamat datang' in response.data or b'Dashboard' in response.data
    
    def test_invalid_login(self, client, admin_user):
        """Test login with invalid credentials"""
        response = client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Username atau password salah' in response.data
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        assert b'Username atau password salah' in response.data
    
    def test_logout(self, client, admin_user, auth):
        """Test user logout"""
        # Login first
        auth.login()
        
        # Then logout
        response = auth.logout()
        assert response.status_code == 302  # Redirect after logout
        
        # Try to access protected page
        response = client.get('/admin/dashboard')
        assert response.status_code == 302  # Should redirect to login
    
    def test_login_required_redirect(self, client):
        """Test that protected pages redirect to login"""
        response = client.get('/admin/dashboard')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_role_based_access(self, client, publisher_user, auth):
        """Test role-based access control"""
        # Login as publisher
        response = client.post('/auth/login', data={
            'username': 'publisher_test',
            'password': 'password123'
        })
        
        # Try to access admin page (should be forbidden)
        response = client.get('/admin/users')
        assert response.status_code == 403 or response.status_code == 302
    
    def test_password_hashing(self, app, admin_user):
        """Test that passwords are properly hashed"""
        with app.app_context():
            user = User.query.filter_by(username='admin_test').first()
            assert user.password_hash != 'password123'  # Should be hashed
            assert user.check_password('password123')  # Should verify correctly
            assert not user.check_password('wrongpassword')  # Should fail for wrong password

class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self, app):
        """Test user creation"""
        with app.app_context():
            role = Role.query.filter_by(name='publisher').first()
            user = User(
                username='testuser',
                email='test@example.com',
                full_name='Test User',
                role_id=role.id
            )
            user.set_password('testpassword')
            
            db.session.add(user)
            db.session.commit()
            
            # Verify user was created
            created_user = User.query.filter_by(username='testuser').first()
            assert created_user is not None
            assert created_user.email == 'test@example.com'
            assert created_user.full_name == 'Test User'
            assert created_user.check_password('testpassword')
    
    def test_user_permissions(self, app, admin_user, publisher_user):
        """Test user permission checking"""
        with app.app_context():
            admin = User.query.filter_by(username='admin_test').first()
            publisher = User.query.filter_by(username='publisher_test').first()
            
            # Admin should have all permissions
            assert admin.has_permission('users', 'create')
            assert admin.has_permission('content', 'publish')
            
            # Publisher should have limited permissions
            assert publisher.has_permission('content', 'create')
            assert not publisher.has_permission('users', 'create')
    
    def test_user_role_methods(self, app, admin_user, editor_user, publisher_user):
        """Test user role checking methods"""
        with app.app_context():
            admin = User.query.filter_by(username='admin_test').first()
            editor = User.query.filter_by(username='editor_test').first()
            publisher = User.query.filter_by(username='publisher_test').first()
            
            # Test admin methods
            assert admin.is_admin()
            assert admin.is_editor()
            assert admin.is_publisher()
            
            # Test editor methods
            assert not editor.is_admin()
            assert editor.is_editor()
            assert editor.is_publisher()
            
            # Test publisher methods
            assert not publisher.is_admin()
            assert not publisher.is_editor()
            assert publisher.is_publisher()
    
    def test_user_to_dict(self, app, admin_user):
        """Test user serialization"""
        with app.app_context():
            user = User.query.filter_by(username='admin_test').first()
            user_dict = user.to_dict()
            
            assert 'id' in user_dict
            assert 'username' in user_dict
            assert 'email' in user_dict
            assert 'full_name' in user_dict
            assert 'role' in user_dict
            assert 'password_hash' not in user_dict  # Should not include password

class TestRoleModel:
    """Test Role model functionality"""
    
    def test_role_permissions(self, app):
        """Test role permission checking"""
        with app.app_context():
            admin_role = Role.query.filter_by(name='admin').first()
            publisher_role = Role.query.filter_by(name='publisher').first()
            
            # Admin role should have user management permissions
            assert admin_role.has_permission('users', 'create')
            assert admin_role.has_permission('content', 'publish')
            
            # Publisher role should not have user management permissions
            assert not publisher_role.has_permission('users', 'create')
            assert publisher_role.has_permission('content', 'create')