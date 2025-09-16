from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional
from app.core.validators import UniqueUsername, UniqueEmail, StrongPassword, OptionalYouTubeURL

class UserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=50),
        UniqueUsername()
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(),
        UniqueEmail()
    ])
    full_name = StringField('Nama Lengkap', validators=[
        DataRequired(), 
        Length(min=2, max=100)
    ])
    phone = StringField('Nomor Telepon', validators=[Length(max=20)])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('active', 'Aktif'),
        ('inactive', 'Tidak Aktif'),
        ('suspended', 'Suspended')
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        Optional(),
        StrongPassword()
    ])
    password2 = PasswordField('Konfirmasi Password', validators=[
        EqualTo('password', message='Password tidak sama')
    ])
    submit = SubmitField('Simpan')

class CategoryForm(FlaskForm):
    name = StringField('Nama Kategori', validators=[
        DataRequired(), 
        Length(min=2, max=100)
    ])
    description = TextAreaField('Deskripsi', validators=[Length(max=500)])
    color = StringField('Warna', validators=[
        DataRequired(),
        Length(min=7, max=7)
    ], default='#28a745')
    is_active = BooleanField('Aktif', default=True)
    sort_order = StringField('Urutan', validators=[Optional()], default='0')
    submit = SubmitField('Simpan')

class SettingForm(FlaskForm):
    site_name = StringField('Nama Website', validators=[
        DataRequired(), 
        Length(min=2, max=100)
    ])
    site_description = TextAreaField('Deskripsi Website', validators=[
        Length(max=500)
    ])
    contact_email = StringField('Email Kontak', validators=[
        DataRequired(), 
        Email()
    ])
    contact_phone = StringField('Nomor Telepon', validators=[
        DataRequired(),
        Length(max=20)
    ])
    address = TextAreaField('Alamat', validators=[
        DataRequired(),
        Length(max=500)
    ])
    submit = SubmitField('Simpan Pengaturan')

class AdminContentForm(FlaskForm):
    """Admin content form with additional fields like author selection and status"""
    title = StringField('Judul', validators=[
        DataRequired(), 
        Length(min=5, max=255)
    ])
    excerpt = TextAreaField('Ringkasan', validators=[
        Length(max=500)
    ])
    content = TextAreaField('Konten', validators=[
        DataRequired(),
        Length(min=10)
    ])
    category_id = SelectField('Kategori', coerce=int, validators=[DataRequired()])
    author_id = SelectField('Penulis', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('pending_review', 'Menunggu Review'),
        ('published', 'Dipublikasi'),
        ('rejected', 'Ditolak')
    ], validators=[DataRequired()], default='published')
    cover_image = FileField('Cover Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Hanya file gambar yang diperbolehkan!')
    ])
    youtube_url = StringField('URL YouTube', validators=[
        Optional(),
        OptionalYouTubeURL()
    ])
    submit = SubmitField('Simpan')