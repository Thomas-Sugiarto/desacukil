from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.blueprints.auth import bp
from app.blueprints.auth.forms import LoginForm, ProfileForm, ChangePasswordForm, RegisterForm
from app.models.user import User
from app import db

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            
            # Redirect based on user role
            if not next_page:
                if user.is_admin():
                    next_page = url_for('admin.dashboard')
                elif user.is_editor():
                    next_page = url_for('editor.dashboard')
                elif user.is_publisher():
                    next_page = url_for('publisher.dashboard')
                else:
                    next_page = url_for('public.index')
            
            flash(f'Selamat datang, {user.full_name}!', 'success')
            return redirect(next_page)
        else:
            flash('Username atau password salah', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Only admin can register new users
    if not current_user.is_admin():
        flash('Anda tidak memiliki izin untuk mengakses halaman ini', 'error')
        return redirect(url_for('public.index'))
    
    form = RegisterForm()
    
    # Get available roles from User model or create simple choices
    role_choices = [
        (1, 'Admin'),
        (2, 'Editor'), 
        (3, 'Publisher'),
        (4, 'User')
    ]
    form.role_id.choices = role_choices
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            bio=form.bio.data,
            role_id=form.role_id.data
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'User {user.username} berhasil didaftarkan', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Terjadi kesalahan saat mendaftarkan user', 'error')
    
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah berhasil logout', 'success')
    return redirect(url_for('public.index'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.bio = form.bio.data
        
        try:
            db.session.commit()
            flash('Profil berhasil diperbarui', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Terjadi kesalahan saat memperbarui profil', 'error')
    
    # Pre-populate form with current user data
    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.email.data = current_user.email
        form.phone.data = current_user.phone
        form.bio.data = current_user.bio
    
    return render_template('auth/profile.html', form=form)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            try:
                db.session.commit()
                flash('Password berhasil diubah', 'success')
                return redirect(url_for('auth.profile'))
            except Exception as e:
                db.session.rollback()
                flash('Terjadi kesalahan saat mengubah password', 'error')
        else:
            flash('Password saat ini tidak benar', 'error')
    
    return render_template('auth/change_password.html', form=form)