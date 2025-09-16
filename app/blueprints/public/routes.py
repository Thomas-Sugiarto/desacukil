from flask import render_template, request, flash, redirect, url_for, abort, current_app
from app.blueprints.public import bp
from app.blueprints.public.forms import ContactForm, SearchForm
from app.models.content import Content, Category
from app.models.setting import Setting
from app.core.email import send_contact_email, send_auto_reply_email
from app import db
from sqlalchemy import or_

@bp.route('/')
def index():
    # Get featured/latest content
    featured_content = Content.query.filter_by(status='published').order_by(
        Content.published_at.desc()
    ).limit(6).all()
    
    # Get content by categories
    categories = Category.query.filter_by(is_active=True).order_by(
        Category.sort_order, Category.name
    ).all()
    
    content_by_category = {}
    for category in categories:
        content_by_category[category.slug] = Content.query.filter_by(
            category_id=category.id, 
            status='published'
        ).order_by(Content.published_at.desc()).limit(3).all()
    
    # Get site settings
    site_settings = Setting.get_public_settings()
    
    return render_template('public/index.html', 
                         featured_content=featured_content,
                         categories=categories,
                         content_by_category=content_by_category,
                         site_settings=site_settings)

@bp.route('/berita')
def berita():
    return category_content('berita')

@bp.route('/kegiatan')
def kegiatan():
    return category_content('kegiatan')

@bp.route('/pengumuman')
def pengumuman():
    return category_content('pengumuman')

@bp.route('/layanan')
def layanan():
    return category_content('layanan')

@bp.route('/category/<slug>')
def category_content(slug):
    category = Category.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    
    content = Content.query.filter_by(
        category_id=category.id, 
        status='published'
    ).order_by(Content.published_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('public/category.html', 
                         category=category, 
                         content=content)

@bp.route('/content/<slug>')
def content_detail(slug):
    content = Content.query.filter_by(slug=slug, status='published').first_or_404()
    
    # Increment view count
    content.view_count += 1
    db.session.commit()
    
    # Get related content from same category
    related_content = Content.query.filter(
        Content.category_id == content.category_id,
        Content.id != content.id,
        Content.status == 'published'
    ).order_by(Content.published_at.desc()).limit(3).all()
    
    return render_template('public/content_detail.html', 
                         content=content,
                         related_content=related_content)

@bp.route('/search')
def search():
    form = SearchForm()
    
    # Populate category choices
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    form.category.choices = [(0, 'Semua Kategori')] + [(cat.id, cat.name) for cat in categories]
    
    query = request.args.get('query', '', type=str)
    category_id = request.args.get('category', 0, type=int)
    page = request.args.get('page', 1, type=int)
    
    content = None
    if query:
        content_query = Content.query.filter(
            Content.status == 'published',
            or_(
                Content.title.contains(query),
                Content.content.contains(query),
                Content.excerpt.contains(query)
            )
        )
        
        if category_id > 0:
            content_query = content_query.filter(Content.category_id == category_id)
        
        content = content_query.order_by(Content.published_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
    
    return render_template('public/search.html', 
                         form=form,
                         content=content,
                         query=query,
                         category_id=category_id)

@bp.route('/about')
def about():
    site_settings = Setting.get_public_settings()
    return render_template('public/about.html', site_settings=site_settings)

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    site_settings = Setting.get_public_settings()
    
    if form.validate_on_submit():
        try:
            # Send email to admin using the contact form data
            admin_success = send_contact_email(
                name=form.name.data,
                email=form.email.data,
                subject=form.subject.data,
                message=form.message.data,
                phone=form.phone.data if hasattr(form, 'phone') and form.phone.data else None
            )
            
            # Send auto-reply to user
            user_success = send_auto_reply_email(
                name=form.name.data,
                email=form.email.data,
                subject=form.subject.data
            )
            
            if admin_success:
                flash('✅ Terima kasih! Pesan Anda telah berhasil dikirim. Kami akan merespons segera.', 'success')
                current_app.logger.info(f'Contact form submitted by {form.name.data} ({form.email.data}) - Admin email: {"✅" if admin_success else "❌"}, Auto-reply: {"✅" if user_success else "❌"}')
                
                if not user_success:
                    current_app.logger.warning(f'Auto-reply failed for {form.email.data}')
            else:
                flash('❌ Maaf, terjadi kesalahan saat mengirim pesan. Silakan coba lagi nanti atau hubungi kami langsung.', 'error')
                current_app.logger.error(f'Failed to send contact form from {form.name.data} ({form.email.data})')
                
        except Exception as e:
            flash('❌ Maaf, terjadi kesalahan sistem. Silakan coba lagi nanti atau hubungi kami langsung.', 'error')
            current_app.logger.error(f'Contact form error: {str(e)}')
        
        return redirect(url_for('public.contact'))
    
    return render_template('public/contact.html', 
                         form=form, 
                         site_settings=site_settings)

@bp.context_processor
def inject_global_vars():
    """Inject global variables into all templates"""
    categories = Category.query.filter_by(is_active=True).order_by(
        Category.sort_order, Category.name
    ).all()
    
    site_settings = Setting.get_public_settings()
    
    return dict(
        nav_categories=categories,
        site_settings=site_settings
    )