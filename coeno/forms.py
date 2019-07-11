from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from coeno.models import User


class CompanyRegistrationForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class MemberRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    title = StringField('Title')
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')

class PostForm(FlaskForm):
    type = SelectField('Type', choices=[('suggestion', 'Suggestion'), ('notion', 'Notion')], validators=[DataRequired()])
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    topic = StringField('Topic', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    content = HiddenField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class DecisionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    topic = StringField('Topic', validators=[DataRequired()])
    submit = SubmitField('Create Decision')

class StepForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = HiddenField('Content', validators=[DataRequired()])
    number = SelectField('Step Number (max 7)', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7')], validators=[DataRequired()])
    submit = SubmitField('Add Step')

class FeedbackForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    topic = StringField('Topic', validators=[DataRequired()])
    content = HiddenField('Content', validators=[DataRequired()])
    submit = SubmitField('Create Request')

class CommentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = HiddenField('Content', validators=[DataRequired()])
    type = SelectField('Feedback Type', choices=[('support', 'I support'), ('agree', 'I agree'), ('recognize', 'I recognize'), ('disagree', 'I disagree')], validators=[DataRequired()])
    submit = SubmitField('Add Comment')

class PollForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    topic = StringField('Topic', validators=[DataRequired()])
    submit = SubmitField('Create Poll')

class PollItemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    submit = SubmitField('Add Poll Item')

class ResponseForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = HiddenField('Content', validators=[DataRequired()])
    submit = SubmitField('Submit Response')

class FindLogin(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Find')

class UpdateCompanyForm(FlaskForm):
    name = StringField('Company Name',
                           validators=[DataRequired(), Length(min=2, max=20)])
    picture = FileField('Update Company Picture', validators=[FileAllowed(['jpg', 'png'])])
    departments = StringField('Company Departments (separate with commas)', validators=[DataRequired()])
    submit = SubmitField('Update Company Profile')
