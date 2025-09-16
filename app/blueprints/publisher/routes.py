from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.blueprints.publisher import bp
from app.blueprints.publisher.forms import ContentForm
from app.models.content import Content, Category
from app.models.audit import AuditLog
from app.core.decorators import publisher_required
from app.core.helpers import save_uploaded_file, delete_uploaded_file, make_slug
from app import db
from datetime import datetime
from sqlalchemy import func

@bp.route('/dashboard')
@login_required
@publisher_required
def dashboard():
    try:
        # Get publisher statistics
        stats = {
            'draft_count': Content.query.filter_by(author_id=current_user.id, status='draft').count(),
            'pending_count': Content.query.filter_by(author_id=current_user.id, status='pending_review').count(),
            'published_count': Content.query.filter_by(author_id=current_user.id, status='published').count(),
            'rejected_count': Content.query.filter_by(author_id=current_user.id, status='rejected').count(),
            'total_views': db.session.query(func.sum(Content.view_count))\
                .filter_by(author_id=current_user.id).scalar() or 0
        }
        
        # Recent content by this publisher
        recent_content = Content.query.filter_by(author_id=current_user.id).order_by(
            Content.created_at.desc()
        ).limit(5).all()
        
        # Recent published content (all publishers)
        recent_published = Content.query.filter_by(status='published').order_by(
            Content.published_at.desc()
        ).limit(5).all()
        
        # Content by category for this publisher
        content_by_category = db.session.query(
            Category.name,
            func.count(Content.id).label('count')
        ).join(Content).filter(
            Content.author_id == current_user.id
        ).group_by(Category.id, Category.name).all()
        
        return render_template('publisher/dashboard.html', 
                             stats=stats,
                             recent_content=recent_content,
                             recent_published=recent_published,
                             content_by_category=content_by_category)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('publisher/dashboard.html', 
                             stats={},
                             recent_content=[],
                             recent_published=[],
                             content_by_category=[])

@bp.route('/')
@login_required
@publisher_required
def index():
    return redirect(url_for('publisher.dashboard'))

@bp.route('/drafts')
@login_required
@publisher_required
def drafts():
    """Show publisher's draft content"""
    try:
        page = request.args.get('page', 1, type=int)
        
        content = Content.query.filter_by(
            author_id=current_user.id, 
            status='draft'
        ).order_by(Content.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        
        # Get categories for filter dropdown
        categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
        
        return render_template('publisher/content_list.html', 
                             content=content,
                             categories=categories,
                             title='Draft Konten',
                             status_filter='draft')
    except Exception as e:
        flash(f'Error loading drafts: {str(e)}', 'error')
        return redirect(url_for('publisher.dashboard'))

@bp.route('/pending')
@login_required
@publisher_required
def pending():
    """Show publisher's pending review content"""
    try:
        page = request.args.get('page', 1, type=int)
        
        content = Content.query.filter_by(
            author_id=current_user.id, 
            status='pending_review'
        ).order_by(Content.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        
        # Get categories for filter dropdown
        categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
        
        return render_template('publisher/content_list.html', 
                             content=content,
                             categories=categories,
                             title='Konten Menunggu Review',
                             status_filter='pending_review')
    except Exception as e:
        flash(f'Error loading pending content: {str(e)}', 'error')
        return redirect(url_for('publisher.dashboard'))

@bp.route('/published')
@login_required
@publisher_required
def published():
    """Show publisher's published content"""
    try:
        page = request.args.get('page', 1, type=int)
        
        content = Content.query.filter_by(
            author_id=current_user.id, 
            status='published'
        ).order_by(Content.published_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        
        # Get categories for filter dropdown
        categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
        
        return render_template('publisher/content_list.html', 
                             content=content,
                             categories=categories,
                             title='Konten Dipublikasi',
                             status_filter='published')
    except Exception as e:
        flash(f'Error loading published content: {str(e)}', 'error')
        return redirect(url_for('publisher.dashboard'))

@bp.route('/rejected')
@login_required
@publisher_required
def rejected():
    """Show publisher's rejected content"""
    try:
        page = request.args.get('page', 1, type=int)
        
        content = Content.query.filter_by(
            author_id=current_user.id, 
            status='rejected'
        ).order_by(Content.updated_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
        
        # Get categories for filter dropdown
        categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
        
        return render_template('publisher/content_list.html', 
                             content=content,
                             categories=categories,
                             title='Konten Ditolak',
                             status_filter='rejected')
    except Exception as e:
        flash(f'Error loading rejected content: {str(e)}', 'error')
        return redirect(url_for('publisher.dashboard'))

@bp.route('/content')
@login_required
@publisher_required
def content_list():
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', '', type=str)
        category_filter = request.args.get('category', '', type=str)
        search = request.args.get('search', '', type=str)
        sort = request.args.get('sort', 'newest', type=str)
        
        # Base query - only show publisher's own content
        query = Content.query.filter_by(author_id=current_user.id)
        
        # Apply filters
        if status_filter:
            query = query.filter(Content.status == status_filter)
        
        if category_filter:
            query = query.filter(Content.category_id == category_filter)
        
        if search:
            query = query.filter(
                db.or_(
                    Content.title.contains(search),
                    Content.content.contains(search)
                )
            )
        
        # Apply sorting
        if sort == 'oldest':
            query = query.order_by(Content.created_at.asc())
        elif sort == 'title':
            query = query.order_by(Content.title.asc())
        elif sort == 'status':
            query = query.order_by(Content.status.asc())
        else:  # newest (default)
            query = query.order_by(Content.created_at.desc())
        
        content = query.paginate(page=page, per_page=10, error_out=False)
        
        # Get categories for filter dropdown
        categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
        
        return render_template('publisher/content_list.html', 
                             content=content,
                             categories=categories,
                             status_filter=status_filter,
                             category_filter=category_filter,
                             search=search,
                             sort=sort,
                             title='Semua Konten')
    except Exception as e:
        flash(f'Error loading content: {str(e)}', 'error')
        return redirect(url_for('publisher.dashboard'))

@bp.route('/content/new', methods=['GET', 'POST'])
@login_required
@publisher_required
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
            
            # Determine status based on button clicked
            status = 'draft'
            if 'submit_review' in request.form:
                status = 'pending_review'
            
            # Create new content
            content = Content(
                title=form.title.data,
                excerpt=form.excerpt.data or None,
                content=form.content.data,
                category_id=form.category_id.data,
                cover_image=cover_filename,
                youtube_url=form.youtube_url.data.strip() if form.youtube_url.data else None,
                author_id=current_user.id,
                status=status
            )
            
            # Generate unique slug
            content.slug = Content.generate_slug_from_title(content.title)
            
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
            
            if status == 'draft':
                flash('Konten berhasil disimpan sebagai draft.', 'success')
            else:
                flash('Konten berhasil dikirim untuk review.', 'success')
            
            return redirect(url_for('publisher.content_list'))
            
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal membuat konten: {str(e)}', 'error')
    
    return render_template('publisher/content_form.html', form=form, title='Buat Konten Baru')

@bp.route('/content/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@publisher_required
def edit_content(id):
    content = Content.query.get_or_404(id)
    
    # Check ownership
    if content.author_id != current_user.id:
        flash('Anda tidak memiliki akses ke konten ini.', 'error')
        return redirect(url_for('publisher.content_list'))
    
    # Publisher can only edit draft and rejected content
    if content.status not in ['draft', 'rejected']:
        flash('Anda hanya dapat mengedit konten dengan status draft atau ditolak.', 'error')
        return redirect(url_for('publisher.content_list'))
    
    form = ContentForm(obj=content)
    
    try:
        # Populate category choices
        categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.name).all()
        form.category_id.choices = [(cat.id, cat.name) for cat in categories]
        
        if form.validate_on_submit():
            old_values = content.to_dict()
            
            # Handle file upload
            if form.cover_image.data:
                if content.cover_image:
                    delete_uploaded_file(content.cover_image)
                content.cover_image = save_uploaded_file(form.cover_image.data, 'content')
            
            # Update content
            content.title = form.title.data
            content.slug = Content.generate_slug_from_title(content.title)
            content.excerpt = form.excerpt.data or None
            content.content = form.content.data
            content.category_id = form.category_id.data
            content.youtube_url = form.youtube_url.data.strip() if form.youtube_url.data else None
            content.updated_at = datetime.utcnow()
            
            # Handle status change
            if 'submit_review' in request.form and content.status in ['draft', 'rejected']:
                content.status = 'pending_review'
                content.review_comment = None  # Clear previous review comments
            
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
            
            if content.status == 'pending_review':
                flash('Konten berhasil diperbarui dan dikirim untuk review.', 'success')
            else:
                flash('Konten berhasil diperbarui.', 'success')
            
            return redirect(url_for('publisher.content_list'))
            
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal memperbarui konten: {str(e)}', 'error')
    
    return render_template('publisher/content_form.html', form=form, title='Edit Konten', content=content)

@bp.route('/content/<int:id>')
@login_required
@publisher_required
def view_content(id):
    content = Content.query.get_or_404(id)
    
    # Check ownership
    if content.author_id != current_user.id:
        flash('Anda tidak memiliki akses ke konten ini.', 'error')
        return redirect(url_for('publisher.content_list'))
    
    return render_template('publisher/content_detail.html', content=content)

@bp.route('/content/<int:id>/preview')
@login_required
@publisher_required
def preview_content(id):
    content = Content.query.get_or_404(id)
    
    # Check ownership
    if content.author_id != current_user.id:
        flash('Anda tidak memiliki akses ke konten ini.', 'error')
        return redirect(url_for('publisher.content_list'))
    
    return render_template('publisher/content_preview.html', content=content)

@bp.route('/content/<int:id>/delete', methods=['POST'])
@login_required
@publisher_required
def delete_content(id):
    try:
        content = Content.query.get_or_404(id)
        
        # Check ownership
        if content.author_id != current_user.id:
            return jsonify({'success': False, 'message': 'Anda tidak memiliki akses ke konten ini.'})
        
        # Publisher can only delete draft content
        if content.status != 'draft':
            return jsonify({'success': False, 'message': 'Anda hanya dapat menghapus konten dengan status draft.'})
        
        old_values = content.to_dict()
        title = content.title
        
        # Delete cover image if exists
        if content.cover_image:
            delete_uploaded_file(content.cover_image)
        
        db.session.delete(content)
        db.session.commit()
        
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
        except Exception:
            pass
        
        return jsonify({'success': True, 'message': f'Konten "{title}" berhasil dihapus.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Gagal menghapus konten: {str(e)}'})

@bp.route('/content/<int:id>/submit-review', methods=['POST'])
@login_required
@publisher_required
def submit_for_review(id):
    try:
        content = Content.query.get_or_404(id)
        
        # Check ownership
        if content.author_id != current_user.id:
            return jsonify({'success': False, 'message': 'Anda tidak memiliki akses ke konten ini.'})
        
        # Can only submit draft or rejected content for review
        if content.status not in ['draft', 'rejected']:
            return jsonify({'success': False, 'message': 'Konten ini tidak dapat dikirim untuk review.'})
        
        old_values = content.to_dict()
        content.status = 'pending_review'
        content.review_comment = None  # Clear previous review comments
        content.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log status change
        try:
            AuditLog.log_action(
                user_id=current_user.id,
                action='submit_for_review',
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
        
        return jsonify({'success': True, 'message': 'Konten berhasil dikirim untuk review.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Gagal mengirim konten untuk review: {str(e)}'})

@bp.route('/analytics')
@login_required
@publisher_required
def analytics():
    try:
        # Get analytics data for publisher's content
        total_content = Content.query.filter_by(author_id=current_user.id).count()
        total_views = db.session.query(func.sum(Content.view_count))\
            .filter_by(author_id=current_user.id).scalar() or 0
        
        # Content by status
        status_stats = db.session.query(
            Content.status,
            func.count(Content.id).label('count')
        ).filter_by(author_id=current_user.id).group_by(Content.status).all()
        
        # Content by category
        category_stats = db.session.query(
            Category.name,
            func.count(Content.id).label('count'),
            func.sum(Content.view_count).label('total_views')
        ).join(Content).filter(
            Content.author_id == current_user.id
        ).group_by(Category.id, Category.name).all()
        
        # Monthly content creation
        monthly_stats = db.session.query(
            func.date_format(Content.created_at, '%Y-%m').label('month'),
            func.count(Content.id).label('count')
        ).filter_by(author_id=current_user.id).group_by('month').order_by('month').all()
        
        return render_template('publisher/analytics.html',
                             total_content=total_content,
                             total_views=total_views,
                             status_stats=status_stats,
                             category_stats=category_stats,
                             monthly_stats=monthly_stats)
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return redirect(url_for('publisher.dashboard'))