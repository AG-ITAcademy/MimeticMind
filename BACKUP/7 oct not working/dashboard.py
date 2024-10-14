from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Project, db

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    projects = Project.query.filter_by(user_id=current_user.id, status='active').all()
    return render_template('dashboard.html', projects=projects)

@dashboard_bp.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    project.status = 'deleted'  # Or db.session.delete(project) if you want to completely remove it
    db.session.commit()
    flash('Project deleted successfully', 'success')
    return redirect(url_for('dashboard_bp.dashboard'))