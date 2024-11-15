from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm
from models import db, User, SubscriptionTier
from flask_mail import Message
from flask import current_app
from config import Config 
from subscription_routes import create_or_update_subscription


access_control_bp = Blueprint('access_control', __name__)


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    try:
        current_app.extensions['mail'].send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

def generate_confirmation_token(email):
    return Config.SERIALIZER.dumps(email, salt='email-confirm-salt')


def confirm_token(token, expiration=3600):
    try:
        email = Config.SERIALIZER.loads(
            token,
            salt='email-confirm-salt',
            max_age=expiration
        )
    except Exception:
        return False
    return email

def generate_reset_token(email):
    return Config.SERIALIZER.dumps(email, salt='password-reset-salt')

def confirm_reset_token(token, expiration=3600):
    try:
        email = Config.SERIALIZER.loads(
            token,
            salt='password-reset-salt',
            max_age=expiration
        )
    except Exception:
        return False
    return email

@access_control_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if not current_user.is_confirmed:
            logout_user()
            flash('Please confirm your account before logging in.', 'warning')
            return redirect(url_for('access_control.login'))
        return redirect(url_for('dashboard_bp.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and check_password_hash(user.password, form.password.data):
            if not user.is_confirmed:
                flash('Check your email for the confirmation link or click Resend.', 'warning')
                return redirect(url_for('access_control.unconfirmed', email=user.email))
            
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard_bp.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html', form=form)
    
@access_control_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data.lower()).first()
        if existing_user and existing_user.is_confirmed:
            flash('Email address is already registered and confirmed. Please use a different email or try logging in.', 'danger')
            return redirect(url_for('access_control.register'))
        try:
            if existing_user:
                existing_user.password = generate_password_hash(form.password.data)
                new_user = existing_user
            else:
                new_user = User(full_name=form.fullname.data, email=form.email.data.lower(), password=generate_password_hash(form.password.data))
                db.session.add(new_user)
            
            db.session.commit()
            
            # Use the new create_or_update_subscription function
            success, message = create_or_update_subscription(new_user.id, SubscriptionTier.STARTER.value)
            if not success:
                raise Exception(message)
            
            token = generate_confirmation_token(new_user.email)
            confirm_url = url_for('access_control.confirm_email', token=token, _external=True)
            html = render_template('activate.html', confirm_url=confirm_url)
            subject = "Please confirm your email"
            send_email(new_user.email, subject, html)
            
            flash('Please check your inbox and confirm your account before logging in.', 'success')
            return redirect(url_for('access_control.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in registration: {str(e)}")
            flash('An unexpected error occurred. Please try again later.', 'danger')
            return redirect(url_for('access_control.register'))
    return render_template('register.html', form=form)
    
@access_control_bp.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('access_control.login'))

    user = User.query.filter_by(email=email).first_or_404()
    if user.is_confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.is_confirmed = True
        db.session.commit()
        flash('Your account is confirmed. You may login now!', 'success')
    return redirect(url_for('access_control.login'))

@access_control_bp.route('/unconfirmed')
@access_control_bp.route('/unconfirmed/<email>')
def unconfirmed(email=None):
    if current_user.is_authenticated and current_user.is_confirmed:
        return redirect(url_for('dashboard_bp.dashboard'))
    return render_template('unconfirmed.html', email=email)
    
@access_control_bp.route('/resend_confirmation')
def resend_confirmation():
    email = request.args.get('email')
    if not email:
        flash('Email address is required.', 'danger')
        return redirect(url_for('access_control.login'))
    
    user = User.query.filter_by(email=email).first()
    if not user or user.is_confirmed:
        return redirect(url_for('access_control.login'))
    
    token = generate_confirmation_token(user.email)
    confirm_url = url_for('access_control.confirm_email', token=token, _external=True)
    html = render_template('activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(user.email, subject, html)
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('access_control.login'))
    
@access_control_bp.route('/reset', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('access_control.reset_token', token=token, _external=True)
            html = render_template('reset_email.html', reset_url=reset_url)
            subject = "Password Reset Request"
            send_email(user.email, subject, html)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('access_control.login'))
    return render_template('reset_request.html', form=form)

@access_control_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_bp.dashboard'))
    
    email = confirm_reset_token(token)
    if email is False:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('access_control.reset_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            hashed_password = generate_password_hash(form.password.data)
            user.password = hashed_password
            db.session.commit()
            flash('Your password has been updated! You can now log in with your new password.', 'success')
            return redirect(url_for('access_control.login'))
        else:
            flash('User not found.', 'danger')
            return redirect(url_for('access_control.reset_request'))
    
    return render_template('reset_token.html', form=form)

@access_control_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('access_control.login'))
    
    
