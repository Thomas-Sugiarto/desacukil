from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired, Length, Optional
from app.core.validators import OptionalYouTubeURL

class ContentForm(FlaskForm):
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
    cover_image = FileField('Cover Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Hanya file gambar yang diperbolehkan!')
    ])
    youtube_url = StringField('URL YouTube', validators=[
        Optional(),
        OptionalYouTubeURL()
    ])
    submit = SubmitField('Simpan')

class ReviewForm(FlaskForm):
    action = RadioField('Action', 
                       choices=[('approve', 'Setujui dan Publikasikan'), 
                               ('reject', 'Tolak Konten')],
                       validators=[DataRequired()])
    review_comment = TextAreaField('Komentar Review', validators=[
        Length(max=1000)
    ])
    submit = SubmitField('Kirim Review')