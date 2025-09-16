from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from app.core.validators import UniqueUsername, UniqueEmail, StrongPassword

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
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
    password = PasswordField('Password', validators=[
        DataRequired(),
        StrongPassword()
    ])
    password2 = PasswordField('Konfirmasi Password', validators=[
        DataRequired(),
        EqualTo('password', message='Password tidak sama')
    ])
    submit = SubmitField('Daftar')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Password Saat Ini', validators=[DataRequired()])
    new_password = PasswordField('Password Baru', validators=[
        DataRequired(),
        StrongPassword()
    ])
    new_password2 = PasswordField('Konfirmasi Password Baru', validators=[
        DataRequired(),
        EqualTo('new_password', message='Password tidak sama')
    ])
    submit = SubmitField('Ubah Password')

class ProfileForm(FlaskForm):
    full_name = StringField('Nama Lengkap', validators=[
        DataRequired(), 
        Length(min=2, max=100)
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email(),
        UniqueEmail()
    ])
    phone = StringField('Nomor Telepon', validators=[Length(max=20)])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    submit = SubmitField('Simpan Profil')