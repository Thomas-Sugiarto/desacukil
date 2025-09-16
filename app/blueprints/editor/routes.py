from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf, CSRFError
from app.blueprints.editor import bp
from app.blueprints.editor.forms import ContentForm, ReviewForm
from app.models.content import Content, Category
from app.models.user import User
from app.models.audit import AuditLog
from app.core.decorators import editor_required
from app.core.helpers import save_uploaded_file, delete_uploaded_file, make_slug
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import logging

# Configure detailed logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@bp.route('/dashboard')
@login_required
@editor_required
def dashboard():
    try:
        # Get today's date for accurate filtering
        today = datetime.utcnow().date()
        
        # Get editor statistics - FIXED with accurate calculations
        stats = {
            # Only count content that is actually pending review
            'pending_review': Content.query.filter_by(status='pending_review').count(),
            
            # Only count content that was approved (published) today
            'approved_today': Content.query.filter(
                Content.status == 'published',
                func.date(Content.published_at) == today
            ).count(),
            
            # Only count content that is currently published (not rejected/draft)
            'published_content': Content.query.filter_by(status='published').count(),
            
            # Count reviews done by this editor this month (both approved and rejected)
            'reviews_this_month': Content.query.filter(
                Content.reviewer_id == current_user.id,
                func.date(Content.updated_at) >= datetime.utcnow().replace(day=1).date()
            ).count(),
            
            # Total reviews by this editor
            'my_reviews': Content.query.filter_by(reviewer_id=current_user.id).count(),
            
            # Content authored by this editor
            'my_content': Content.query.filter_by(author_id=current_user.id).count(),
            
            # Total views only from published content
            'total_views': db.session.query(func.sum(Content.view_count)).filter(
                Content.status == 'published'
            ).scalar() or 0
        }
        
        # Recent content pending review (oldest first for priority)
        pending_content = Content.query.filter_by(status='pending_review').order_by(
            Content.created_at.asc()
        ).limit(5).all()
        
        # Recently published content (newest first)
        recent_published = Content.query.filter_by(status='published').order_by(
            Content.published_at.desc()
        ).limit(5).all()
        
        # Recent activity by this editor (content they reviewed)
        recent_reviews = Content.query.filter_by(reviewer_id=current_user.id).order_by(
            Content.updated_at.desc()
        ).limit(5).all()
        
        # Content by category (only published content)
        content_by_category = db.session.query(
            Category.name,
            func.count(Content.id).label('count')
        ).join(Content).filter(
            Content.status == 'published'
        ).group_by(Category.id, Category.name).all()
        
        return render_template('editor/dashboard.html', 
                             stats=stats,
                             pending_content=pending_content,
                             recent_published=recent_published,
                             recent_reviews=recent_reviews,
                             content_by_category=content_by_category)
                             
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        # Return safe fallback stats
        return render_template('editor/dashboard.html', 
                             stats={
                                 'pending_review': 0,
                                 'approved_today': 0,
                                 'published_content': 0,
                                 'reviews_this_month': 0,
                                 'my_reviews': 0,
                                 'my_content': 0,
                                 'total_views': 0
                             },
                             pending_content=[],
                             recent_published=[],
                             recent_reviews=[],
                             content_by_category=[])

@bp.route('/api/pending-count')
@login_required
@editor_required
def api_pending_count():
    """API endpoint to get current pending review count"""
    try:
        count = Content.query.filter_by(status='pending_review').count()
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/')
@login_required
@editor_required
def index():
    return redirect(url_for('editor.dashboard'))

@bp.route('/review-queue')
@login_required
@editor_required
def review_queue():
    try:
        page = request.args.get('page', 1, type=int)
        category_filter = request.args.get('category', '', type=str)
        author_filter = request.args.get('author', '', type=str)
        sort = request.args.get('sort', 'oldest', type=str)
        
        # Base query for pending review content
        query = Content.query.filter_by(status='pending_review')
        
        # Apply filters
        if category_filter:
            query = query.filter(Content.category_id == category_filter)
        
        if author_filter:
            query = query.filter(Content.author_id == author_filter)
        
        # Apply sorting
        if sort == 'newest':
            query = query.order_by(Content.created_at.desc())
        elif sort == 'title':
            query = query.order_by(Content.title.asc())
        elif sort == 'author':
            query = query.join(User, Content.author_id == User.id).order_by(User.full_name.asc())
        else:  # oldest (default for review queue)
            query = query.order_by(Content.created_at.asc())
        
        content = query.paginate(page=page, per_page=10, error_out=False)
        
        # Get data for filters
        categories = Category.query.filter_by(is_active=True).all()
        authors = db.session.query(User).join(Content, Content.author_id == User.id)\
            .filter(Content.status == 'pending_review').distinct().all()
        
        return render_template('editor/review_queue.html', 
                             content=content, 
                             categories=categories,
                             authors=authors,
                             category_filter=category_filter,
                             author_filter=author_filter,
                             sort=sort)
    except Exception as e:
        flash(f'Error loading review queue: {str(e)}', 'error')
        return redirect(url_for('editor.dashboard'))

@bp.route('/content')
@login_required
@editor_required
def content_list():
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', '', type=str)
        category_filter = request.args.get('category', '', type=str)
        author_filter = request.args.get('author', '', type=str)
        search = request.args.get('search', '', type=str)
        sort = request.args.get('sort', 'newest', type=str)
        
        # Base query - editors can see all content
        query = Content.query
        
        # Apply filters
        if status_filter:
            query = query.filter(Content.status == status_filter)
        
        if category_filter:
            query = query.filter(Content.category_id == category_filter)
        
        if author_filter:
            query = query.filter(Content.author_id == author_filter)
        
        if search:
            query = query.filter(
                or_(
                    Content.title.contains(search),
                    Content.content.contains(search)
                )
            )
        
        # Apply sorting
        if sort == 'oldest':
            query = query.order_by(Content.created_at.asc())
        elif sort == 'title':
            query = query.order_by(Content.title.asc())
        elif sort == 'author':
            query = query.join(User, Content.author_id == User.id).order_by(User.full_name.asc())
        elif sort == 'status':
            query = query.order_by(Content.status.asc())
        else:  # newest (default)
            query = query.order_by(Content.created_at.desc())
        
        content = query.paginate(page=page, per_page=20, error_out=False)
        
        # Get additional data for filters
        categories = Category.query.filter_by(is_active=True).all()
        authors = db.session.query(User).join(Content, Content.author_id == User.id).distinct().all()
        pending_count = Content.query.filter_by(status='pending_review').count()
        
        return render_template('editor/content_list.html', 
                             content=content,
                             categories=categories,
                             authors=authors,
                             pending_count=pending_count,
                             status_filter=status_filter,
                             category_filter=category_filter,
                             author_filter=author_filter,
                             search=search,
                             sort=sort)
    except Exception as e:
        flash(f'Error loading content: {str(e)}', 'error')
        return redirect(url_for('editor.dashboard'))

@bp.route('/content/<int:id>')
@login_required
@editor_required
def view_content(id):
    try:
        content = Content.query.get_or_404(id)
        
        # Increment view count
        content.view_count += 1
        db.session.commit()
        
        return render_template('editor/content_detail.html', content=content)
    except Exception as e:
        flash(f'Error viewing content: {str(e)}', 'error')
        return redirect(url_for('editor.content_list'))

@bp.route('/content/<int:id>/review', methods=['GET', 'POST'])
@login_required
@editor_required
def content_review(id):
    try:
        content = Content.query.get_or_404(id)
        
        if content.status != 'pending_review':
            flash('Konten ini tidak dalam status menunggu review.', 'error')
            return redirect(url_for('editor.review_queue'))
        
        form = ReviewForm()
        
        if form.validate_on_submit():
            action = form.action.data
            comment = form.review_comment.data
            
            old_values = content.to_dict()
            
            if action == 'approve':
                if content.approve(current_user):
                    flash('Konten berhasil disetujui dan dipublikasi.', 'success')
                    
                    # Log approval
                    AuditLog.log_action(
                        user_id=current_user.id,
                        action='approve_content',
                        table_name='content',
                        record_id=content.id,
                        old_values=old_values,
                        new_values=content.to_dict(),
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string
                    )
                else:
                    flash('Gagal menyetujui konten.', 'error')
            
            elif action == 'reject':
                if content.reject(current_user, comment):
                    flash('Konten berhasil ditolak.', 'info')
                    
                    # Log rejection
                    AuditLog.log_action(
                        user_id=current_user.id,
                        action='reject_content',
                        table_name='content',
                        record_id=content.id,
                        old_values=old_values,
                        new_values=content.to_dict(),
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string
                    )
                else:
                    flash('Gagal menolak konten.', 'error')
            
            db.session.commit()
            return redirect(url_for('editor.review_queue'))
        
        return render_template('editor/review_content.html', content=content, form=form)
    except Exception as e:
        db.session.rollback()
        flash(f'Error reviewing content: {str(e)}', 'error')
        return redirect(url_for('editor.review_queue'))

@bp.route('/content/new', methods=['GET', 'POST'])
@login_required
@editor_required
def create_content():
    form = ContentForm()
    
    try:
        # Populate category choices
        categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.name).all()
        form.category_id.choices = [(cat.id, cat.name) for cat in categories]
        
        if form.validate_on_submit():
            # Handle file upload
            cover_filename = None
            if form.cover_image.data:
                cover_filename = save_uploaded_file(form.cover_image.data, 'content')
            
            # Create new content
            content = Content(
                title=form.title.data,
                excerpt=form.excerpt.data,
                content=form.content.data,
                category_id=form.category_id.data,
                cover_image=cover_filename,
                youtube_url=form.youtube_url.data.strip() if form.youtube_url.data else None,
                author_id=current_user.id,
                status='published'  # Editor can directly publish
            )
            
            # Generate unique slug
            content.slug = Content.generate_slug_from_title(content.title)
            
            if content.status == 'published':
                content.published_at = datetime.utcnow()
            
            db.session.add(content)
            db.session.commit()
            
            # Log content creation
            try:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action='create_content',
                    table_name='content',
                    record_id=content.id,
                    new_values=content.to_dict(),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.commit()
            except Exception:
                pass
            
            flash('Konten berhasil dibuat dan dipublikasi.', 'success')
            return redirect(url_for('editor.content_list'))
        
        return render_template('editor/content_form.html', form=form, title='Buat Konten Baru')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal membuat konten: {str(e)}', 'error')
        return redirect(url_for('editor.content_list'))

@bp.route('/content/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@editor_required
def edit_content(id):
    try:
        content = Content.query.get_or_404(id)
        form = ContentForm(obj=content)
        
        # Populate category choices
        categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.name).all()
        form.category_id.choices = [(cat.id, cat.name) for cat in categories]
        
        if form.validate_on_submit():
            old_values = content.to_dict()
            
            # Handle file upload
            if form.cover_image.data:
                # Delete old cover image
                if content.cover_image:
                    delete_uploaded_file(content.cover_image)
                
                content.cover_image = save_uploaded_file(form.cover_image.data, 'content')
            
            # Update content
            content.title = form.title.data
            content.slug = Content.generate_slug_from_title(content.title)
            content.excerpt = form.excerpt.data
            content.content = form.content.data
            content.category_id = form.category_id.data
            content.youtube_url = form.youtube_url.data.strip() if form.youtube_url.data else None
            content.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Log content update
            try:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action='update_content',
                    table_name='content',
                    record_id=content.id,
                    old_values=old_values,
                    new_values=content.to_dict(),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.commit()
            except Exception:
                pass
            
            flash('Konten berhasil diperbarui.', 'success')
            return redirect(url_for('editor.content_list'))
        
        return render_template('editor/content_form.html', form=form, title='Edit Konten', content=content)
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal memperbarui konten: {str(e)}', 'error')
        return redirect(url_for('editor.content_list'))

@bp.route('/content/<int:id>/delete', methods=['POST', 'DELETE'])
@login_required
@editor_required
def delete_content(id):
    """Enhanced delete route with comprehensive debugging"""
    logger.debug("=== DELETE CONTENT REQUEST START ===")
    logger.debug(f"Content ID: {id}")
    logger.debug(f"Request Method: {request.method}")
    logger.debug(f"Content-Type: {request.content_type}")
    logger.debug(f"Is JSON: {request.is_json}")
    logger.debug(f"Remote Address: {request.remote_addr}")
    logger.debug(f"User Agent: {request.user_agent}")
    
    # Log all headers
    logger.debug("=== REQUEST HEADERS ===")
    for header_name, header_value in request.headers:
        logger.debug(f"{header_name}: {header_value}")
    
    # Log request data
    logger.debug("=== REQUEST DATA ===")
    logger.debug(f"Form Data: {dict(request.form)}")
    logger.debug(f"JSON Data: {request.get_json(silent=True)}")
    logger.debug(f"Raw Data: {request.data}")
    
    try:
        # Check authentication first
        if not current_user.is_authenticated:
            logger.error("User not authenticated")
            return jsonify({
                'success': False, 
                'message': 'User not authenticated',
                'debug_info': {'error_type': 'authentication_error'}
            }), 401
        
        logger.debug(f"Authenticated user: {current_user.id} ({current_user.username})")
        
        # Check permissions
        if not current_user.has_permission('content', 'delete'):
            logger.error("User lacks delete permission")
            return jsonify({
                'success': False, 
                'message': 'Anda tidak memiliki izin untuk menghapus konten',
                'debug_info': {'error_type': 'permission_error'}
            }), 403
        
        logger.debug("Permission check passed")
        
        # CSRF validation with detailed logging
        csrf_token = None
        
        # Try multiple ways to get CSRF token
        csrf_sources = {
            'X-CSRFToken header': request.headers.get('X-CSRFToken'),
            'X-CSRF-Token header': request.headers.get('X-CSRF-Token'),
            'csrf_token form field': request.form.get('csrf_token'),
            'csrf_token JSON field': request.get_json(silent=True).get('csrf_token') if request.get_json(silent=True) else None
        }
        
        logger.debug("=== CSRF TOKEN SOURCES ===")
        for source, token in csrf_sources.items():
            logger.debug(f"{source}: {token}")
            if token and not csrf_token:
                csrf_token = token
        
        if not csrf_token:
            logger.error("CSRF token not found in any source")
            return jsonify({
                'success': False, 
                'message': 'CSRF token missing',
                'debug_info': {
                    'error_type': 'csrf_missing',
                    'csrf_sources': csrf_sources,
                    'headers': dict(request.headers),
                    'method': request.method,
                    'content_type': request.content_type
                }
            }), 400
        
        logger.debug(f"Using CSRF token: {csrf_token}")
        
        # Validate CSRF token
        try:
            validate_csrf(csrf_token)
            logger.debug("CSRF validation successful")
        except CSRFError as e:
            logger.error(f"CSRF validation failed: {e}")
            return jsonify({
                'success': False, 
                'message': f'CSRF validation failed: {str(e)}',
                'debug_info': {
                    'error_type': 'csrf_validation_error',
                    'csrf_error': str(e),
                    'csrf_token': csrf_token
                }
            }), 400
        
        # Check if content exists
        content = Content.query.get(id)
        if not content:
            logger.error(f"Content with ID {id} not found")
            return jsonify({
                'success': False, 
                'message': 'Konten tidak ditemukan',
                'debug_info': {'error_type': 'content_not_found'}
            }), 404
        
        logger.debug(f"Content found: {content.title}")
        
        # Store content info for response
        old_values = content.to_dict()
        title = content.title
        
        # Delete cover image if exists
        if content.cover_image:
            try:
                delete_uploaded_file(content.cover_image)
                logger.debug(f"Cover image deleted: {content.cover_image}")
            except Exception as e:
                logger.warning(f"Could not delete cover image {content.cover_image}: {str(e)}")
        
        # Delete content from database
        db.session.delete(content)
        db.session.commit()
        logger.debug("Content deleted from database")
        
        # Log content deletion
        try:
            AuditLog.log_action(
                user_id=current_user.id,
                action='delete_content',
                table_name='content',
                record_id=id,
                old_values=old_values,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.commit()
            logger.debug("Audit log created")
        except Exception as e:
            logger.warning(f"Could not create audit log: {str(e)}")
        
        logger.debug("=== DELETE CONTENT SUCCESS ===")
        return jsonify({
            'success': True, 
            'message': f'Konten "{title}" berhasil dihapus.'
        })
        
    except Exception as e:
        db.session.rollback()
        error_message = f'Gagal menghapus konten: {str(e)}'
        logger.error(f"Unexpected error in delete_content: {error_message}")
        logger.exception("Full traceback:")
        
        return jsonify({
            'success': False, 
            'message': error_message,
            'debug_info': {
                'error_type': 'unexpected_error',
                'exception': str(e),
                'content_id': id
            }
        }), 500

@bp.route('/content/<int:id>/publish', methods=['POST'])
@login_required
@editor_required
def publish_content(id):
    try:
        content = Content.query.get_or_404(id)
        old_values = content.to_dict()
        
        if content.status in ['draft', 'rejected']:
            content.status = 'published'
            content.published_at = datetime.utcnow()
            content.reviewer_id = current_user.id
            
            db.session.commit()
            
            # Log publishing
            try:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action='publish_content',
                    table_name='content',
                    record_id=content.id,
                    old_values=old_values,
                    new_values=content.to_dict(),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.commit()
            except Exception:
                pass
            
            return jsonify({'success': True, 'message': f'Konten "{content.title}" berhasil dipublikasi.'})
        else:
            return jsonify({'success': False, 'message': 'Konten tidak dapat dipublikasi.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Gagal mempublikasi konten: {str(e)}'})

@bp.route('/content/<int:id>/unpublish', methods=['POST'])
@login_required
@editor_required
def unpublish_content(id):
    try:
        content = Content.query.get_or_404(id)
        old_values = content.to_dict()
        
        if content.status == 'published':
            content.status = 'draft'
            content.published_at = None
            
            db.session.commit()
            
            # Log unpublishing
            try:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action='unpublish_content',
                    table_name='content',
                    record_id=content.id,
                    old_values=old_values,
                    new_values=content.to_dict(),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.commit()
            except Exception:
                pass
            
            return jsonify({'success': True, 'message': f'Konten "{content.title}" berhasil di-unpublish.'})
        else:
            return jsonify({'success': False, 'message': 'Konten tidak dapat di-unpublish.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Gagal meng-unpublish konten: {str(e)}'})

@bp.route('/bulk-action', methods=['POST'])
@login_required
@editor_required
def bulk_action():
    try:
        # Validate CSRF token for AJAX requests
        if request.is_json:
            try:
                validate_csrf(request.headers.get('X-CSRFToken'))
            except CSRFError as e:
                return jsonify({
                    'success': False, 
                    'message': 'CSRF token missing or invalid'
                }), 400
        
        action = request.json.get('action')
        content_ids = request.json.get('content_ids', [])
        
        if not action or not content_ids:
            return jsonify({'success': False, 'message': 'Data tidak lengkap'})
        
        contents = Content.query.filter(Content.id.in_(content_ids)).all()
        success_count = 0
        
        for content in contents:
            old_values = content.to_dict()
            
            if action == 'publish':
                if content.status in ['draft', 'rejected', 'pending_review']:
                    content.status = 'published'
                    content.published_at = datetime.utcnow()
                    content.reviewer_id = current_user.id
                    success_count += 1
            elif action == 'unpublish':
                if content.status == 'published':
                    content.status = 'draft'
                    content.published_at = None
                    success_count += 1
            elif action == 'delete':
                if content.cover_image:
                    try:
                        delete_uploaded_file(content.cover_image)
                    except Exception:
                        pass  # Continue with deletion even if file removal fails
                db.session.delete(content)
                success_count += 1
                continue
            elif action == 'pending':
                if content.status in ['draft', 'rejected']:
                    content.status = 'pending_review'
                    success_count += 1
            
            # Log the action
            try:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action=f'bulk_{action}',
                    table_name='content',
                    record_id=content.id,
                    old_values=old_values,
                    new_values=content.to_dict() if action != 'delete' else None,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
            except Exception:
                pass
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Berhasil memproses {success_count} konten'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/review-history')
@login_required
@editor_required
def review_history():
    try:
        page = request.args.get('page', 1, type=int)
        
        # Get content reviewed by this editor
        reviewed_content = Content.query.filter_by(reviewer_id=current_user.id).order_by(
            Content.updated_at.desc()
        ).paginate(page=page, per_page=20, error_out=False)
        
        # Calculate statistics for the template
        stats = {
            'approved': Content.query.filter_by(reviewer_id=current_user.id, status='published').count(),
            'rejected': Content.query.filter_by(reviewer_id=current_user.id, status='rejected').count(),
            'this_month': Content.query.filter(
                Content.reviewer_id == current_user.id,
                func.date(Content.updated_at) >= datetime.utcnow().replace(day=1).date()
            ).count(),
            'total': Content.query.filter_by(reviewer_id=current_user.id).count()
        }
        
        return render_template('editor/review_history.html', 
                             reviews=reviewed_content,
                             stats=stats)
    except Exception as e:
        flash(f'Error loading review history: {str(e)}', 'error')
        return redirect(url_for('editor.dashboard'))

@bp.route('/analytics')
@login_required
@editor_required
def analytics():
    try:
        # Get comprehensive analytics for editors
        total_content = Content.query.count()
        total_views = db.session.query(func.sum(Content.view_count)).scalar() or 0
        
        # Content by status
        status_stats = db.session.query(
            Content.status,
            func.count(Content.id).label('count')
        ).group_by(Content.status).all()
        
        # Content by category
        category_stats = db.session.query(
            Category.name,
            func.count(Content.id).label('count'),
            func.sum(Content.view_count).label('total_views')
        ).join(Content).group_by(Category.id, Category.name).all()
        
        # Top authors
        author_stats = db.session.query(
            User.full_name,
            func.count(Content.id).label('content_count'),
            func.sum(Content.view_count).label('total_views')
        ).join(Content, Content.author_id == User.id)\
        .group_by(User.id, User.full_name)\
        .order_by(func.count(Content.id).desc()).limit(10).all()
        
        # Monthly content statistics
        monthly_stats = db.session.query(
            func.date_format(Content.created_at, '%Y-%m').label('month'),
            func.count(Content.id).label('count')
        ).group_by('month').order_by('month').all()
        
        return render_template('editor/analytics.html',
                             total_content=total_content,
                             total_views=total_views,
                             status_stats=status_stats,
                             category_stats=category_stats,
                             author_stats=author_stats,
                             monthly_stats=monthly_stats)
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return redirect(url_for('editor.dashboard'))