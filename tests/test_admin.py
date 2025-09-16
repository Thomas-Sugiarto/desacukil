"""
Admin functionality tests for CMS Desa
"""

import pytest
from flask import url_for
from app.models.user import User, Role
from app.models.setting import Setting
from app import db

class TestAdminAccess:
    """Test admin access control"""
    
    def test_admin_dashboard_access(self, client, admin_user):
        """Test admin can access dashboard"""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        })
        
        response = client.get('/admin/dashboard')
        assert response.status_code == 200
        assert b'Dashboard Admin' in response.data or b'Admin' in response.data
    
    def test_non_admin_dashboard_denied(self, client, publisher_user):
        """Test non-admin cannot access admin dashboard"""
        # Login as publisher
        client.post('/auth/login', data={
            'username': 'publisher_test',
            'password': 'password123'
        })
        
        response = client.get('/admin/dashboard')
        assert response.status_code == 403 or response.status_code == 302
    
    def test_unauthenticated_admin_redirect(self, client):
        """Test unauthenticated user redirected from admin"""
        response = client.get('/admin/dashboard')
        assert response.status_code == 302
        assert '/auth/login' in response.location

class TestUserManagement:
    """Test admin user management functionality"""
    
    def test_user_list_view(self, client, admin_user):
        """Test admin can view user list"""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        })
        
        response = client.get('/admin/users')
        assert response.status_code == 200
        assert b'admin_test' in response.data
    
    def test_user_creation_form(self, client, admin_user):
        """Test admin can access user creation form"""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        })
        
        response = client.get('/admin/users/new')
        assert response.status_code == 200
        assert b'Tambah User' in response.data or b'Username' in response.data
    
    def test_user_creation(self, client, admin_user):
        """Test admin can create new users"""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        })
        
        # Get publisher role ID
        with client.application.app_context():
            publisher_role = Role.query.filter_by(name='publisher').first()
            role_id = publisher_role.id
        
        # Create new user
        response = client.post('/admin/users/new', data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'full_name': 'New User',
            'role_id': role_id,
            'status': 'active',
            'password': 'password123',
            'password2': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify user was created
        with client.application.app_context():
            new_user = User.query.filter_by(username='newuser').first()
            assert new_user is not None
            assert new_user.email == 'newuser@test.com'
    
    def test_user_edit(self, client, admin_user, publisher_user):
        """Test admin can edit users"""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        })
        
        # Edit publisher user
        response = client.get(f'/admin/users/{publisher_user.id}/edit')
        assert response.status_code == 200
        assert b'Edit User' in response.data or b'publisher_test' in response.data
        
        # Update user
        with client.application.app_context():
            publisher_role = Role.query.filter_by(name='publisher').first()
            
        response = client.post(f'/admin/users/{publisher_user.id}/edit', data={
            'username': 'publisher_test',
            'email': 'updated@test.com',
            'full_name': 'Updated Publisher',
            'role_id': publisher_role.id,
            'status': 'active'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify user was updated
        with client.application.app_context():
            updated_user = User.query.get(publisher_user.id)
            assert updated_user.email == 'updated@test.com'
            assert updated_user.full_name == 'Updated Publisher'
    
    def test_user_deletion(self, client, admin_user, publisher_user):
        """Test admin can delete users"""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        })
        
        user_id = publisher_user.id
        
        # Delete user
        response = client.post(f'/admin/users/{user_id}/delete', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify user was deleted
        with client.application.app_context():
            deleted_user = User.query.get(user_id)
            assert deleted_user is None

class TestSettingsManagement:
    """Test admin settings management"""
    
    def test_settings_view(self, client, admin_user):
        """Test admin can view settings"""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        })
        
        response = client.get('/admin/settings')
        assert response.status_code == 200
        assert b'Pengaturan' in response.data or b'Settings' in response.data
    
    def test_settings_update(self, client, admin_user):
        """Test admin can update settings"""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        })
        
        # Update settings
        response = client.post('/admin/settings', data={
            'site_name': 'Updated Site Name',
            'site_description': 'Updated description',
            'contact_email': 'updated@test.com',
            'contact_phone': '123-456-7890',
            'address': 'Updated Address'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify settings were updated
        with client.application.app_context():
            site_name = Setting.get_value('site_name')
            assert site_name == 'Updated Site Name'

class TestAuditLogs:
    """Test audit log functionality"""
    
    def test_audit_logs_view(self, client, admin_user):
        """Test admin can view audit logs"""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        })
        
        response = client.get('/admin/audit-logs')
        assert response.status_code == 200
        assert b'Log Audit' in response.data or b'Audit' in response.data
    
    def test_audit_log_creation(self, app, admin_user):
        """Test audit logs are created for admin actions"""
        from app.models.audit import AuditLog
        
        with app.app_context():
            # Create an audit log entry
            log = AuditLog.log_action(
                user_id=admin_user.id,
                action='create',
                table_name='users',
                record_id=1,
                new_values={'username': 'testuser'},
                ip_address='127.0.0.1',
                user_agent='Test Agent'
            )
            db.session.commit()
            
            # Verify log was created
            created_log = AuditLog.query.filter_by(
                user_id=admin_user.id,
                action='create'
            ).first()
            
            assert created_log is not None
            assert created_log.table_name == 'users'
            assert created_log.ip_address == '127.0.0.1'

class TestDashboardStats:
    """Test admin dashboard statistics"""
    
    def test_dashboard_statistics(self, client, admin_user, published_content, test_content):
        """Test dashboard shows correct statistics"""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        })
        
        response = client.get('/admin/dashboard')
        assert response.status_code == 200
        
        # Should show user count, content counts, etc.
        # The exact assertions depend on the dashboard template structure
        assert b'Total' in response.data or b'Konten' in response.data
    
    def test_dashboard_recent_content(self, client, admin_user, published_content):
        """Test dashboard shows recent content"""
        # Login as admin
        client.post('/auth/login', data={
            'username': 'admin_test',
            'password': 'password123'
        })
        
        response = client.get('/admin/dashboard')
        assert response.status_code == 200
        assert b'Published Content' in response.data