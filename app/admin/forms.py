from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
from app import db
from app.models import Department, Subject

class DepartmentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    submit = SubmitField('Submit')

class SubjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    code = StringField('Code', validators=[DataRequired(), Length(max=20)])
    description = TextAreaField('Description')
    department_id = SelectField('Department', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(SubjectForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(d.id, d.name) for d in Department.query.all()]

class MaterialForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    file = FileField('File', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'docx', 'pptx', 'txt', 'jpg', 'png'], 'Only specific file types are allowed!')
    ])
    submit = SubmitField('Upload')

    def __init__(self, *args, **kwargs):
        super(MaterialForm, self).__init__(*args, **kwargs)
        self.subject_id.choices = [(s.id, f"{s.department.name} - {s.name}") for s in Subject.query.all()] 