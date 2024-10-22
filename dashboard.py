from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Project, db, Population, FilterModel, ProjectSurvey
from flask_wtf.csrf import CSRFProtect
    
dashboard_bp = Blueprint('dashboard_bp', __name__)
csrf = CSRFProtect()

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    projects = Project.query.filter_by(user_id=current_user.id, status='active').all()
    populations = Population.query.all()
    return render_template('dashboard.html', projects=projects, populations=populations)

@dashboard_bp.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    try:
        project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
        segments_count = FilterModel.query.filter_by(project_id=project_id).count()
        surveys_count = ProjectSurvey.query.filter_by(project_id=project_id).count()
        db.session.begin_nested()
        ProjectSurvey.query.filter_by(project_id=project_id).delete()
        FilterModel.query.filter_by(project_id=project_id).delete()
        project.status = 'deleted'
        db.session.commit()
        message_parts = [f"Project '{project.name}' has been deleted"]
        if segments_count > 0 or surveys_count > 0:
            message_parts.append("along with")
            deleted_items = []
            if segments_count > 0:
                deleted_items.append(f"{segments_count} segment{'s' if segments_count != 1 else ''}")
            if surveys_count > 0:
                deleted_items.append(f"{surveys_count} survey{'s' if surveys_count != 1 else ''}")
            message_parts.append(" and ".join(deleted_items))
        
        flash(f"{' '.join(message_parts)}.", "success")
        return redirect(url_for('dashboard_bp.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the project: {str(e)}", "danger")
        return redirect(url_for('dashboard_bp.dashboard'))