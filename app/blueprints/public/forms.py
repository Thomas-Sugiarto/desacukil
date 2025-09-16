from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email

class ContactForm(FlaskForm):
    name = StringField('Nama', validators=[
        DataRequired(), 
        Length(min=2, max=100)
    ])
    email = StringField('Email', validators=[
        DataRequired(), 
        Email()
    ])
    subject = StringField('Subjek', validators=[
        DataRequired(), 
        Length(min=5, max=200)
    ])
    message = TextAreaField('Pesan', validators=[
        DataRequired(),
        Length(min=10, max=1000)
    ])
    phone = StringField('Nomor Telepon', validators=[
        DataRequired(),
        Length(min=10, max=15)                
    ])
    submit = SubmitField('Kirim Pesan')


class SearchForm(FlaskForm):
    query = StringField('Pencarian', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])
    category = SelectField('Kategori', coerce=int, validators=[])
    submit = SubmitField('Cari')