#forms.py
''' forms used in various modules '''

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, SelectField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from models import User

class SurveyForm(FlaskForm):
    """
    Form for creating and editing surveys.
    Handles basic survey metadata and configuration settings.
    """
    name = StringField('Survey Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    context_prompt = TextAreaField('Context Prompt')
    survey_id = HiddenField()

class FilterForm(FlaskForm):
    """
    Form for defining demographic and characteristic-based filters.
    Used to segment survey populations based on various criteria.
    """
    alias = StringField('Segment Name', validators=[DataRequired()])
    
    # These fields will be dynamically populated with database values
    gender = SelectField('Gender', validators=[Optional()])
    location = SelectField('Location', validators=[Optional()])
    ethnicity = SelectField('Ethnicity', validators=[Optional()])
    occupation = SelectField('Occupation', validators=[Optional()])
    education_level = SelectField('Education Level', validators=[Optional()])
    religion = SelectField('Religion', validators=[Optional()])
    health_status = SelectField('Health Status', validators=[Optional()])
    legal_status = SelectField('Legal Status', validators=[Optional()])
    marital_status = SelectField('Marital Status', validators=[Optional()])
    age_min = IntegerField('Age Min', validators=[Optional()])
    age_max = IntegerField('Age Max', validators=[Optional()])
    income_range = SelectField('Income Range', validators=[Optional()], choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')])
    ai_filter=StringField('AI Filter', validators=[Optional()])
    
    submit = SubmitField('CREATE SEGMENT')
    cancel = SubmitField('CANCEL')
    

class RegistrationForm(FlaskForm):
    """
    User registration form with password confirmation and email validation.
    """
    fullname = StringField('Full Name', validators=[DataRequired(), Length(max=150)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    """
    Authentication form for existing users.
    Provides email-based login with optional remember-me functionality.
    """
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class RequestResetForm(FlaskForm):
    """
    Form for initiating password reset process.
    Validates that the provided email exists in the system.
    """
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=150)])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user is None:
            raise ValidationError('There is no account with that email.')

class ResetPasswordForm(FlaskForm):
    """
    Form for setting a new password after reset request.
    Ensures password confirmation matches and meets minimum requirements.
    """
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')
    
class ProjectForm(FlaskForm):
    """
    Form for creating and managing projects.
    Captures basic project information and metadata.
    """
    name = StringField('Project Name', validators=[DataRequired()])
    description = TextAreaField('Project Description')
    create = SubmitField('Create')
    cancel = SubmitField('Cancel')
    
class PopulationFilterForm(FlaskForm):
    """
    UNUSED ***** Form for filtering population demographics.
    Provides demographic and socioeconomic filtering options for population segmentation.
    """
    gender = SelectField('Gender', choices=[('', 'All'), ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    age_min = IntegerField('Age Min', validators=[Optional()])
    age_max = IntegerField('Age Max', validators=[Optional()])
    location = StringField('Location')
    ethnicity = StringField('Ethnicity')
    occupation = StringField('Occupation')
    education_level = StringField('Education')
    religion = StringField('Religion')
    health_status = StringField('Health Status')
    legal_status = StringField('Legal Status')
    marital_status = StringField('Marital Status')
    income_range = SelectField('Income Range', choices=[
        ('', 'All'),
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ])
    
    