from flask import Flask, render_template, redirect, url_for, flash, request, g, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from models import db, User, Project,  Population, SurveyTemplate, SubscriptionTier, Subscription
import os
from flask_migrate import Migrate
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import or_
from projects import projects_bp
from dashboard import dashboard_bp
from survey_builder import survey_builder_bp
from population_explorer import population_explorer_bp
from survey_analysis import survey_analysis_bp
from access_control import access_control_bp
from subscription_routes import subscription_bp
from survey_reports import survey_reports_bp
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
login_manager.login_view = 'access_control.login'

mail = Mail(app)

# User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
@app.context_processor
def inject_global_vars():
    subscription_info = None
    show_tooltips=False
    if current_user.is_authenticated:
        subscription_info = current_user.subscription
        show_tooltips = current_user.tooltips
    return dict(
        projects=g.projects if hasattr(g, 'projects') else [],
        populations=Population.query.all(),
        subscription_info=subscription_info,
        show_tooltips=show_tooltips
    )

# register additional blueprints
app.register_blueprint(projects_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(survey_analysis_bp)
app.register_blueprint(population_explorer_bp)
app.register_blueprint(survey_builder_bp)
app.register_blueprint(access_control_bp)
app.register_blueprint(subscription_bp)
app.register_blueprint(survey_reports_bp)


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
    
@app.route('/pricing')
def pricing():
    return render_template('pricing.html', SubscriptionTier=SubscriptionTier)

@app.route('/api/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({
            'populations': [],
            'projects': [],
            'survey_templates': []
        })

    # Search in populations
    populations = Population.query.filter(
        or_(
            Population.name.ilike(f'%{query}%'),
            Population.description.ilike(f'%{query}%')
        )
    ).all()

    # Search in projects
    projects = Project.query.filter(
        Project.user_id == current_user.id,
        Project.status == 'active',
        or_(
            Project.name.ilike(f'%{query}%'),
            Project.description.ilike(f'%{query}%')
        )
    ).all()

    # Search in survey templates
    survey_templates = SurveyTemplate.query.filter(
        or_(
            SurveyTemplate.user_id == current_user.id,
            SurveyTemplate.user_id == None
        ),
        or_(
            SurveyTemplate.name.ilike(f'%{query}%'),
            SurveyTemplate.description.ilike(f'%{query}%')
        )
    ).all()

    return jsonify({
        'populations': [{'tag': p.tag, 'name': p.name} for p in populations],
        'projects': [{'id': p.id, 'name': p.name} for p in projects],
        'survey_templates': [{'id': s.id, 'name': s.name} for s in survey_templates]
    })

if __name__ == '__main__':
    app.run(debug=True)