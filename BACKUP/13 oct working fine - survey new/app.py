from flask import Flask, render_template, redirect, url_for, flash, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, ProjectForm, RequestResetForm, ResetPasswordForm
from models import db, User, Project, ProfileModel,  Population
import os
from flask_migrate import Migrate
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from flask import render_template_string
from projects import projects_bp
from dashboard import dashboard_bp
from survey_builder import survey_builder_bp
from population_explorer import population_explorer_bp
from survey_analysis import survey_analysis_bp
from config import Config
from flask_wtf.csrf import CSRFProtect
import celery_app

import logging

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

db.init_app(app)  
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize serializer
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
mail = Mail(app)

# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
@app.context_processor
def inject_global_vars():
    return dict(
        projects=g.projects if hasattr(g, 'projects') else [],
        populations=Population.query.all()
    )


# register additional blueprints
app.register_blueprint(projects_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(survey_analysis_bp)
app.register_blueprint(population_explorer_bp)
app.register_blueprint(survey_builder_bp)

@app.before_request
def before_request():
    g.user = current_user
    if current_user.is_authenticated:
        g.projects = Project.query.filter_by(user_id=current_user.id, status='active').all()
    else:
        g.projects = []

# Routes
@app.route('/')
def home():
    return redirect(url_for('landing'))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            if not user.is_confirmed:
                return redirect(url_for('unconfirmed'))
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard_bp.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(email=form.email.data.lower(), password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Generate confirmation token
        token = generate_confirmation_token(new_user.email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"

        send_email(new_user.email, subject, html)

        flash('A confirmation email has been sent via email.', 'success')
        return redirect(url_for('unconfirmed'))
    return render_template('register.html', form=form)
    
@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('unconfirmed'))

    user = User.query.filter_by(email=email).first_or_404()
    if user.is_confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.is_confirmed = True
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('login'))

@app.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.is_confirmed:
        return redirect(url_for('dashboard_bp.dashboard'))
    flash('Please confirm your account!', 'warning')
    return render_template('unconfirmed.html')
    
@app.route('/resend')
@login_required
def resend_confirmation():
    token = generate_confirmation_token(current_user.email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(current_user.email, subject, html)
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('unconfirmed'))
    
def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

def generate_confirmation_token(email):
    return s.dumps(email, salt='email-confirm-salt')

def confirm_token(token, expiration=3600):
    try:
        email = s.loads(
            token,
            salt='email-confirm-salt',
            max_age=expiration
        )
    except Exception:
        return False
    return email

def generate_reset_token(email):
    return s.dumps(email, salt='password-reset-salt')

def confirm_reset_token(token, expiration=3600):
    try:
        email = s.loads(
            token,
            salt='password-reset-salt',
            max_age=expiration
        )
    except Exception:
        return False
    return email    
    
@app.route('/reset', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('reset_token', token=token, _external=True)
            html = render_template('reset_email.html', reset_url=reset_url)
            subject = "Password Reset Request"
            send_email(user.email, subject, html)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', form=form)

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))
    email = confirm_reset_token(token)
    if not email:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first_or_404()
        hashed_password = generate_password_hash(form.password.data)
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/notifications')
@login_required
def notifications():
    return render_template('notifications.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')
    
@app.route('/landing')
def landing():
    return render_template('landing.html')

if __name__ == '__main__':
    app.run(debug=True)