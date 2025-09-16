"""
Content management tests for CMS Desa
"""

import pytest
from flask import url_for
from app.models.content import Content, Category
from app.models.user import User
from app import db

class TestContent:
    """Test content functionality"""
    
    def test_content_creation(self, app, publisher_user):
        """Test content creation"""
        with app.app_context():
            category = Category.query.filter_by(slug='test-category').first()
            content = Content(
                title='New Test Content',
                slug='new-test-content',
                content='This is new test content.',
                excerpt='New test excerpt',
                author_id=publisher_user.id,
                category_id=category.id
            )
            
            db.session.add(content)
            db.session.commit()
            
            # Verify content was created
            created_content = Content.query.filter_by(slug='new-test-content').first()
            assert created_content is not None
            assert created_content.title == 'New Test Content'
            assert created_content.status == 'draft'  # Default status
    
    def test_slug_generation(self, app, publisher_user):
        """Test automatic slug generation"""
        with app.app_context():
            category = Category.query.filter_by(slug='test-category').first()
            content = Content(
                title='Test Content with Special Characters!@#',
                author_id=publisher_user.id,
                category_id=category.id,
                content='Test content'
            )
            
            slug = content.generate_slug()
            assert slug == 'test-content-with-special-characters'
    
    def test_content_workflow(self, app, test_content, editor_user):
        """Test content workflow transitions"""
        with app.app_context():
            content = Content.query.filter_by(slug='test-content').first()
            editor = User.query.filter_by(username='editor_test').first()
            
            # Test submit for review
            assert content.status == 'draft'
            success = content.submit_for_review()
            assert success
            assert content.status == 'pending_review'
            
            # Test approval
            success = content.approve(editor)
            assert success
            assert content.status == 'published'
            assert content.reviewer_id == editor.id
            assert content.published_at is not None
    
    def test_content_rejection(self, app, test_content, editor_user):
        """Test content rejection"""
        with app.app_context():
            content = Content.query.filter_by(slug='test-content').first()
            editor = User.query.filter_by(username='editor_test').first()
            
            # Submit for review first
            content.submit_for_review()
            
            # Test rejection
            success = content.reject(editor, 'Content needs improvement')
            assert success
            assert content.status == 'rejected'
            assert content.reviewer_id == editor.id
            assert content.review_comment == 'Content needs improvement'
    
    def test_content_permissions(self, app, test_content, admin_user, publisher_user):
        """Test content edit/delete permissions"""
        with app.app_context():
            content = Content.query.filter_by(slug='test-content').first()
            admin = User.query.filter_by(username='admin_test').first()
            publisher = User.query.filter_by(username='publisher_test').first()
            
            # Author should be able to edit draft
            assert content.can_edit(publisher)
            assert content.can_delete(publisher)
            
            # Admin should be able to edit/delete anything
            assert content.can_edit(admin)
            assert content.can_delete(admin)
            
            # Test with published content
            content.status = 'published'
            assert not content.can_delete(publisher)  # Author can't delete published
            assert content.can_delete(admin)  # Admin can delete anything
    
    def test_youtube_url_extraction(self, app, test_content):
        """Test YouTube URL processing"""
        with app.app_context():
            content = Content.query.filter_by(slug='test-content').first()
            
            # Test various YouTube URL formats
            test_urls = [
                'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'https://youtu.be/dQw4w9WgXcQ',
                'https://youtube.com/embed/dQw4w9WgXcQ'
            ]
            
            for url in test_urls:
                content.youtube_url = url
                video_id = content.get_youtube_embed_id()
                assert video_id == 'dQw4w9WgXcQ'
    
    def test_content_to_dict(self, app, published_content):
        """Test content serialization"""
        with app.app_context():
            content = Content.query.filter_by(slug='published-content').first()
            content_dict = content.to_dict()
            
            assert 'id' in content_dict
            assert 'title' in content_dict
            assert 'slug' in content_dict
            assert 'status' in content_dict
            assert 'author' in content_dict
            assert 'category' in content_dict

class TestContentViews:
    """Test content-related views"""
    
    def test_public_content_list(self, client, published_content):
        """Test public content listing"""
        response = client.get('/')
        assert response.status_code == 200
        # Should show published content
        assert b'Published Content' in response.data
    
    def test_content_detail_view(self, client, published_content):
        """Test content detail view"""
        response = client.get('/content/published-content')
        assert response.status_code == 200
        assert b'Published Content' in response.data
        assert b'Published excerpt' in response.data
    
    def test_draft_content_not_public(self, client, test_content):
        """Test that draft content is not visible to public"""
        response = client.get('/content/test-content')
        assert response.status_code == 404  # Should not be accessible
    
    def test_category_view(self, client, published_content):
        """Test category content listing"""
        response = client.get('/category/test-category')
        assert response.status_code == 200
        assert b'Published Content' in response.data
    
    def test_publisher_content_creation(self, client, publisher_user, auth):
        """Test content creation via web interface"""
        # Login as publisher
        client.post('/auth/login', data={
            'username': 'publisher_test',
            'password': 'password123'
        })
        
        # Access content creation page
        response = client.get('/publisher/content/new')
        assert response.status_code == 200
        assert b'Buat Konten Baru' in response.data
        
        # Create new content
        response = client.post('/publisher/content/new', data={
            'title': 'Web Test Content',
            'content': 'This is content created via web interface.',
            'excerpt': 'Web test excerpt',
            'category_id': 1,
            'save_draft': '1'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'berhasil' in response.data or b'success' in response.data
    
    def test_editor_review_interface(self, client, test_content, editor_user):
        """Test editor review interface"""
        # Submit content for review first
        with client.application.app_context():
            content = Content.query.filter_by(slug='test-content').first()
            content.submit_for_review()
            db.session.commit()
        
        # Login as editor
        client.post('/auth/login', data={
            'username': 'editor_test',
            'password': 'password123'
        })
        
        # Access review queue
        response = client.get('/editor/review-queue')
        assert response.status_code == 200
        assert b'Test Content' in response.data
        
        # Access review page
        response = client.get(f'/editor/content/{test_content.id}/review')
        assert response.status_code == 200
        assert b'Review Konten' in response.data or b'Test Content' in response.data

class TestCategory:
    """Test category functionality"""
    
    def test_category_creation(self, app):
        """Test category creation"""
        with app.app_context():
            category = Category(
                name='New Category',
                slug='new-category',
                description='A new test category',
                color='#ff0000'
            )
            
            db.session.add(category)
            db.session.commit()
            
            # Verify category was created
            created_category = Category.query.filter_by(slug='new-category').first()
            assert created_category is not None
            assert created_category.name == 'New Category'
            assert created_category.color == '#ff0000'
    
    def test_category_to_dict(self, app):
        """Test category serialization"""
        with app.app_context():
            category = Category.query.filter_by(slug='test-category').first()
            category_dict = category.to_dict()
            
            assert 'id' in category_dict
            assert 'name' in category_dict
            assert 'slug' in category_dict
            assert 'color' in category_dict
            assert 'content_count' in category_dict