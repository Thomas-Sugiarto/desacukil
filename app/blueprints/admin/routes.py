from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.blueprints.admin import bp
from app.blueprints.admin.forms import UserForm, CategoryForm, SettingForm, AdminContentForm
from app.models.user import User, Role
from app.models.content import Content, Category, ContentRevision
from app.models.audit import AuditLog
from app.models.setting import Setting
from app.core.decorators import admin_required
from app.core.helpers import save_uploaded_file, delete_uploaded_file
from app import db
from datetime import datetime
from sqlalchemy import func
from flask_wtf import FlaskForm

class DeleteForm(FlaskForm):
    pass

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'total_content': Content.query.count(),
        'published_content': Content.query.filter_by(status='published').count(),
        'pending_content': Content.query.filter_by(status='pending_review').count(),
        'draft_content': Content.query.filter_by(status='draft').count(),
        'rejected_content': Content.query.filter_by(status='rejected').count(),
    }
    
    # Recent content
    recent_content = Content.query.order_by(Content.created_at.desc()).limit(5).all()
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Content by category
    content_by_category = db.session.query(
        Category.name,
        func.count(Content.id).label('count')
    ).outerjoin(Content).group_by(Category.id, Category.name).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_content=recent_content,
                         recent_users=recent_users,
                         content_by_category=content_by_category)

@bp.route('/')
@login_required
@admin_required
def index():
    # Redirect to dashboard
    return redirect(url_for('admin.dashboard'))

# Admin's own content management - separate from editor
@bp.route('/content')
@login_required
@admin_required
def content_list():
    """Admin content management - admin has full access to all content"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    category_filter = request.args.get('category', '', type=str)
    author_filter = request.args.get('author', '', type=str)
    search = request.args.get('search', '', type=str)
    sort = request.args.get('sort', 'newest', type=str)
    
    query = Content.query
    
    if status_filter:
        query = query.filter(Content.status == status_filter)
    
    if category_filter:
        query = query.filter(Content.category_id == category_filter)
    
    if author_filter:
        query = query.filter(Content.author_id == author_filter)
    
    if search:
        query = query.filter(
            db.or_(
                Content.title.contains(search),
                Content.content.contains(search)
            )
        )
    
    # Apply sorting with explicit join condition for author sorting
    if sort == 'oldest':
        query = query.order_by(Content.created_at.asc())
    elif sort == 'title':
        query = query.order_by(Content.title.asc())
    elif sort == 'author':
        # Specify explicit join condition to avoid ambiguity
        query = query.join(User, Content.author_id == User.id).order_by(User.full_name.asc())
    else:  # newest (default)
        query = query.order_by(Content.created_at.desc())
    
    content = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get additional data for filters
    categories = Category.query.filter_by(is_active=True).all()
    
    # Get authors with explicit join to avoid ambiguity
    authors = db.session.query(User).join(Content, Content.author_id == User.id).distinct().all()
    
    # Get pending count for the review queue button
    pending_count = Content.query.filter_by(status='pending_review').count()
    
    return render_template('admin/content_list.html', 
                         content=content,
                         categories=categories,
                         authors=authors,
                         pending_count=pending_count,
                         status_filter=status_filter,
                         category_filter=category_filter,
                         author_filter=author_filter,
                         search=search,
                         sort=sort)

@bp.route('/content/<int:id>')
@login_required
@admin_required
def view_content(id):
    content = Content.query.get_or_404(id)

    # Increment view count
    content.view_count += 1
    db.session.commit()

    # Get 5 latest revisions safely
    try:
        revisions = ContentRevision.query.filter_by(content_id=content.id).order_by(ContentRevision.created_at.desc()).limit(5).all()
    except Exception as e:
        # If there's an issue with revisions, just set empty list
        revisions = []
        flash(f'Warning: Could not load revisions: {str(e)}', 'warning')

    return render_template(
        'admin/content_detail.html',
        content=content,
        revisions=revisions
    )

@bp.route('/content/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_content():
    """Admin create new content"""
    form = AdminContentForm()
    
    # Populate category choices
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.name).all()
    form.category_id.choices = [(cat.id, cat.name) for cat in categories]
    
    # Populate author choices (admin can assign content to any user)
    users = User.query.filter(User.role.has(Role.name.in_(['admin', 'editor', 'publisher']))).order_by(User.full_name).all()
    form.author_id.choices = [(user.id, user.full_name) for user in users]
    form.author_id.data = current_user.id  # Default to current admin
    
    if form.validate_on_submit():
        try:
            # Handle file upload
            cover_filename = None
            if form.cover_image.data:
                cover_filename = save_uploaded_file(form.cover_image.data, 'covers')
            
            # Safely handle title encoding
            title = form.title.data
            if isinstance(title, bytes):
                title = title.decode('utf-8', errors='ignore')
            
            content = Content(
                title=title,
                slug=Content.generate_slug_from_title(title),
                excerpt=form.excerpt.data or '',
                content=form.content.data or '',
                category_id=form.category_id.data,
                cover_image=cover_filename,
                youtube_url=form.youtube_url.data.strip() if form.youtube_url.data else None,
                author_id=form.author_id.data,
                status=form.status.data
            )
            
            if content.status == 'published':
                content.published_at = datetime.utcnow()
            
            db.session.add(content)
            db.session.commit()
            
            # Log content creation
            try:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action='admin_create_content',
                    table_name='content',
                    record_id=content.id,
                    new_values=content.to_dict(),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.commit()
            except Exception as log_error:
                # Don't fail the content creation if logging fails
                flash(f'Content created but logging failed: {str(log_error)}', 'warning')
            
            flash(f'Konten "{content.title}" berhasil dibuat dengan status {content.status}.', 'success')
            return redirect(url_for('admin.content_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal membuat konten: {str(e)}', 'error')
    
    return render_template('admin/content_form.html', form=form, title='Buat Konten Baru')

@bp.route('/content/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_content(id):
    """Admin edit content"""
    content = Content.query.get_or_404(id)
    form = AdminContentForm(obj=content)
    
    # Populate category choices
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.name).all()
    form.category_id.choices = [(cat.id, cat.name) for cat in categories]
    
    # Populate author choices
    users = User.query.filter(User.role.has(Role.name.in_(['admin', 'editor', 'publisher']))).order_by(User.full_name).all()
    form.author_id.choices = [(user.id, user.full_name) for user in users]
    
    if form.validate_on_submit():
        try:
            old_values = content.to_dict()
            
            # Handle file upload
            if form.cover_image.data:
                # Delete old cover image
                if content.cover_image:
                    delete_uploaded_file(content.cover_image)
                
                content.cover_image = save_uploaded_file(form.cover_image.data, 'covers')
            
            # Safely handle title encoding
            title = form.title.data
            if isinstance(title, bytes):
                title = title.decode('utf-8', errors='ignore')
            
            content.title = title
            content.slug = content.generate_slug()
            content.excerpt = form.excerpt.data or ''
            content.content = form.content.data or ''
            content.category_id = form.category_id.data
            content.youtube_url = form.youtube_url.data.strip() if form.youtube_url.data else None
            content.author_id = form.author_id.data
            content.status = form.status.data
            content.updated_at = datetime.utcnow()
            
            # Handle status changes
            if form.status.data == 'published' and content.published_at is None:
                content.published_at = datetime.utcnow()
            elif form.status.data != 'published':
                content.published_at = None
            
            db.session.commit()
            
            # Log content update
            try:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action='admin_update_content',
                    table_name='content',
                    record_id=content.id,
                    old_values=old_values,
                    new_values=content.to_dict(),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.commit()
            except Exception as log_error:
                # Don't fail the content update if logging fails
                flash(f'Content updated but logging failed: {str(log_error)}', 'warning')
            
            flash(f'Konten "{content.title}" berhasil diperbarui.', 'success')
            return redirect(url_for('admin.content_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal memperbarui konten: {str(e)}', 'error')
    
    return render_template('admin/content_form.html', form=form, title='Edit Konten', content=content)

@bp.route('/content/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_content(id):
    """Admin delete content"""
    try:
        content = Content.query.get_or_404(id)
        old_values = content.to_dict()
        
        # Delete cover image if exists
        if content.cover_image:
            delete_uploaded_file(content.cover_image)
        
        title = content.title
        db.session.delete(content)
        db.session.commit()
        
        # Log content deletion
        try:
            AuditLog.log_action(
                user_id=current_user.id,
                action='admin_delete_content',
                table_name='content',
                record_id=id,
                old_values=old_values,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.commit()
        except Exception as log_error:
            # Don't fail the deletion if logging fails
            flash(f'Content deleted but logging failed: {str(log_error)}', 'warning')
        
        flash(f'Konten "{title}" berhasil dihapus.', 'success')
        return redirect(url_for('admin.content_list'))
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus konten: {str(e)}', 'error')
        return redirect(url_for('admin.content_list'))

@bp.route('/content/bulk-action', methods=['POST'])
@login_required
@admin_required
def bulk_action():
    """Admin bulk actions on content"""
    try:
        data = request.get_json()
        action = data.get('action')
        content_ids = data.get('content_ids', [])
        
        if not action or not content_ids:
            return jsonify({'success': False, 'message': 'Data tidak lengkap'})
        
        contents = Content.query.filter(Content.id.in_(content_ids)).all()
        
        for content in contents:
            old_values = content.to_dict()
            
            if action == 'publish':
                content.status = 'published'
                content.published_at = datetime.utcnow()
            elif action == 'unpublish':
                content.status = 'draft'
                content.published_at = None
            elif action == 'pending':
                content.status = 'pending_review'
            elif action == 'delete':
                if content.cover_image:
                    delete_uploaded_file(content.cover_image)
                db.session.delete(content)
                
                # Log deletion
                try:
                    AuditLog.log_action(
                        user_id=current_user.id,
                        action=f'admin_bulk_delete',
                        table_name='content',
                        record_id=content.id,
                        old_values=old_values,
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string
                    )
                except Exception:
                    pass  # Continue even if logging fails
                continue
            
            # Log the action for non-delete operations
            try:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action=f'admin_bulk_{action}',
                    table_name='content',
                    record_id=content.id,
                    old_values=old_values,
                    new_values=content.to_dict(),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
            except Exception:
                pass  # Continue even if logging fails
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Berhasil {action} {len(contents)} konten'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    role_filter = request.args.get('role', '', type=str)
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.full_name.contains(search),
                User.email.contains(search)
            )
        )
    
    if role_filter:
        query = query.join(Role).filter(Role.name == role_filter)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    roles = Role.query.all()
    
    return render_template('admin/users.html', users=users, roles=roles, 
                         search=search, role_filter=role_filter)

@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = UserForm()
    
    # Populate role choices
    roles = Role.query.filter_by(is_active=True).all()
    form.role_id.choices = [(role.id, role.name.title()) for role in roles]
    
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                phone=form.phone.data,
                bio=form.bio.data,
                role_id=form.role_id.data,
                status=form.status.data
            )
            
            if form.password.data:
                user.set_password(form.password.data)
            else:
                user.set_password('password123')
            
            db.session.add(user)
            db.session.commit()
            
            # Log user creation
            try:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action='create_user',
                    table_name='users',
                    record_id=user.id,
                    new_values=user.to_dict(),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.commit()
            except Exception:
                pass
            
            flash(f'User {user.username} berhasil dibuat.', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal membuat user: {str(e)}', 'error')
    
    return render_template('admin/user_form.html', form=form, title='Tambah User')

@bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    form._obj = user
    # Populate role choices
    roles = Role.query.filter_by(is_active=True).all()
    form.role_id.choices = [(role.id, role.name.title()) for role in roles]
    
    if form.validate_on_submit():
        try:
            old_values = user.to_dict()
            
            user.username = form.username.data
            user.email = form.email.data
            user.full_name = form.full_name.data
            user.phone = form.phone.data
            user.bio = form.bio.data
            user.role_id = form.role_id.data
            user.status = form.status.data
            user.updated_at = datetime.utcnow()
            
            if form.password.data:
                user.set_password(form.password.data)
            
            db.session.commit()
            
            # Log user update
            try:
                AuditLog.log_action(
                    user_id=current_user.id,
                    action='update_user',
                    table_name='users',
                    record_id=user.id,
                    old_values=old_values,
                    new_values=user.to_dict(),
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.commit()
            except Exception:
                pass
            
            flash(f'User {user.username} berhasil diperbarui.', 'success')
            return redirect(url_for('admin.users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal memperbarui user: {str(e)}', 'error')
    
    return render_template('admin/user_form.html', form=form, title='Edit User', user=user)

@bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    try:
        user = User.query.get_or_404(id)
        
        # Prevent deleting self
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Anda tidak dapat menghapus akun sendiri.'})
        
        old_values = user.to_dict()
        username = user.username
        
        db.session.delete(user)
        db.session.commit()
        
        # Log user deletion
        try:
            AuditLog.log_action(
                user_id=current_user.id,
                action='delete_user',
                table_name='users',
                record_id=id,
                old_values=old_values,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.commit()
        except Exception:
            pass
        
        return jsonify({'success': True, 'message': f'User {username} berhasil dihapus.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Gagal menghapus user: {str(e)}'})

@bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.order_by(Category.sort_order, Category.name).all()
    form = DeleteForm()  # Add delete form for CSRF token
    return render_template('admin/categories.html', categories=categories, form=form)

@bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    form = CategoryForm()
    
    if form.validate_on_submit():
        try:
            from app.core.helpers import make_slug
            
            category = Category(
                name=form.name.data,
                slug=make_slug(form.name.data),
                description=form.description.data,
                color=form.color.data,
                is_active=form.is_active.data,
                sort_order=int(form.sort_order.data) if form.sort_order.data else 0
            )
            
            db.session.add(category)
            db.session.commit()
            
            flash(f'Kategori {category.name} berhasil dibuat.', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal membuat kategori: {str(e)}', 'error')
    
    return render_template('admin/category_form.html', form=form, title='Tambah Kategori')

@bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        try:
            from app.core.helpers import make_slug
            
            category.name = form.name.data
            category.slug = make_slug(form.name.data)
            category.description = form.description.data
            category.color = form.color.data
            category.is_active = form.is_active.data
            category.sort_order = int(form.sort_order.data) if form.sort_order.data else 0
            
            db.session.commit()
            
            flash(f'Kategori {category.name} berhasil diperbarui.', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal memperbarui kategori: {str(e)}', 'error')
    
    return render_template('admin/category_form.html', form=form, title='Edit Kategori', category=category)

@bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    try:
        category = Category.query.get_or_404(id)
        
        # Check if category has content
        content_count = Content.query.filter_by(category_id=id).count()
        if content_count > 0:
            flash(f'Tidak dapat menghapus kategori {category.name} karena masih digunakan oleh {content_count} konten.', 'error')
            return redirect(url_for('admin.categories'))
        
        old_values = category.to_dict()
        category_name = category.name
        
        db.session.delete(category)
        db.session.commit()
        
        # Log category deletion
        try:
            AuditLog.log_action(
                user_id=current_user.id,
                action='delete',
                table_name='categories',
                record_id=id,
                old_values=old_values,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.commit()
        except Exception:
            pass  # Continue even if logging fails
        
        flash(f'Kategori {category_name} berhasil dihapus.', 'success')
        return redirect(url_for('admin.categories'))
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus kategori: {str(e)}', 'error')
        return redirect(url_for('admin.categories'))

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    form = SettingForm()
    
    # Load current settings
    if request.method == 'GET':
        form.site_name.data = Setting.get_value('site_name', 'Portal Desa Digital')
        form.site_description.data = Setting.get_value('site_description', 'Sistem Informasi dan Layanan Desa')
        form.contact_email.data = Setting.get_value('contact_email', 'info@desa.go.id')
        form.contact_phone.data = Setting.get_value('contact_phone', '021-12345678')
        form.address.data = Setting.get_value('address', 'Jl. Raya Desa No. 123')
    
    if form.validate_on_submit():
        try:
            # Update settings
            Setting.set_value('site_name', form.site_name.data, 'string', 'Nama website desa', True)
            Setting.set_value('site_description', form.site_description.data, 'string', 'Deskripsi website desa', True)
            Setting.set_value('contact_email', form.contact_email.data, 'string', 'Email kontak desa', True)
            Setting.set_value('contact_phone', form.contact_phone.data, 'string', 'Nomor telepon desa', True)
            Setting.set_value('address', form.address.data, 'string', 'Alamat kantor desa', True)
            
            db.session.commit()
            
            flash('Pengaturan berhasil disimpan.', 'success')
            return redirect(url_for('admin.settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menyimpan pengaturan: {str(e)}', 'error')
    
    return render_template('admin/settings.html', form=form)

@bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '', type=str)
    
    query = AuditLog.query
    
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    
    logs = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/audit_logs.html', logs=logs, action_filter=action_filter)