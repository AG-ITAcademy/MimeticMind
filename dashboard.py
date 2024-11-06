from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Project, db, Population, FilterModel, ProjectSurvey, LLM, User
from flask_wtf.csrf import CSRFProtect
    
dashboard_bp = Blueprint('dashboard_bp', __name__)
csrf = CSRFProtect()

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    projects = Project.query.filter_by(
        user_id=current_user.id, 
        status='active'
    ).order_by(Project.created_at.asc()).all()
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
        
        
@dashboard_bp.route('/settings')
@login_required
def settings():
    llms = LLM.query.order_by(LLM.id.asc()).all()  # Order LLMs by ID
    return render_template('settings.html', 
                         llms=llms,
                         current_user=current_user)

@dashboard_bp.route('/update_preferences', methods=['POST'])
@login_required
def update_preferences():
    try:
        llm_id = request.form.get('llm_id', type=int)
        # Fix boolean handling - checkbox values come as 'on' when checked
        tooltips = request.form.get('tooltips') == 'on'
        recommendations = request.form.get('recommendations') == 'on'
        
        user = User.query.get(current_user.id)
        user.llm_id = llm_id
        user.tooltips = tooltips
        user.recommendations = recommendations
        
        db.session.commit()
        flash('Preferences updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating preferences: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard_bp.settings'))