from flask import render_template, request, send_file, flash, redirect, url_for, current_app
from flask_login import current_user
from app.main import bp
from app.models import Department, Subject, Material
from sqlalchemy import or_, desc
import os
from datetime import datetime

@bp.route('/')
def index():
    # Get all departments with their subjects and materials
    departments = Department.query.all()
    
    # Get all subjects
    subjects = Subject.query.all()
    
    # Get all materials
    materials = Material.query.all()
    
    # Calculate total downloads
    total_downloads = sum(material.download_count for material in materials)
    
    # Get recent materials (last 6)
    recent_materials = Material.query.order_by(desc(Material.upload_date)).limit(6).all()
    
    # Add material counts to departments
    for department in departments:
        department.materials = Material.query.join(Subject).filter(Subject.department_id == department.id).all()
    
    return render_template('index.html',
                         departments=departments,
                         subjects=subjects,
                         materials=materials,
                         total_downloads=total_downloads,
                         recent_materials=recent_materials)

@bp.route('/materials')
def materials():
    # Get search parameters
    search = request.args.get('q', '')
    department_id = request.args.get('department', type=int)
    subject_id = request.args.get('subject', type=int)
    file_type = request.args.get('type', '')
    
    # Build query
    query = Material.query
    
    if search:
        query = query.filter(
            or_(
                Material.title.ilike(f'%{search}%'),
                Material.description.ilike(f'%{search}%'),
                Subject.name.ilike(f'%{search}%'),
                Department.name.ilike(f'%{search}%')
            )
        ).join(Subject).join(Department)
    
    if department_id:
        query = query.join(Subject).filter(Subject.department_id == department_id)
    
    if subject_id:
        query = query.filter(Material.subject_id == subject_id)
    
    if file_type:
        query = query.filter(Material.file_type == file_type)
    
    # Order by upload date (newest first)
    materials = query.order_by(desc(Material.upload_date)).all()
    
    # Get departments and subjects for filters
    departments = Department.query.all()
    subjects = Subject.query.all()
    
    return render_template('materials.html',
                         materials=materials,
                         departments=departments,
                         subjects=subjects,
                         search=search,
                         selected_department=department_id,
                         selected_subject=subject_id,
                         selected_type=file_type)

@bp.route('/departments')
def departments():
    departments = Department.query.all()
    
    # Calculate material counts for each department
    for department in departments:
        department.material_count = Material.query.join(Subject).filter(Subject.department_id == department.id).count()
        department.subject_count = Subject.query.filter(Subject.department_id == department.id).count()
    
    return render_template('departments.html', departments=departments)

@bp.route('/department/<int:id>')
def department(id):
    department = Department.query.get_or_404(id)
    materials = Material.query.join(Subject).filter(Subject.department_id == id).order_by(desc(Material.upload_date)).all()
    
    return render_template('department.html', department=department, materials=materials)

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    
    if not query:
        return redirect(url_for('main.materials'))
    
    # Search in materials, subjects, and departments
    materials = Material.query.filter(
        or_(
            Material.title.ilike(f'%{query}%'),
            Material.description.ilike(f'%{query}%'),
            Subject.name.ilike(f'%{query}%'),
            Department.name.ilike(f'%{query}%')
        )
    ).join(Subject).join(Department).order_by(desc(Material.upload_date)).all()
    
    # Search departments
    departments = Department.query.filter(
        or_(
            Department.name.ilike(f'%{query}%'),
            Department.description.ilike(f'%{query}%')
        )
    ).all()
    
    # Search subjects
    subjects = Subject.query.filter(
        or_(
            Subject.name.ilike(f'%{query}%'),
            Subject.description.ilike(f'%{query}%'),
            Subject.code.ilike(f'%{query}%')
        )
    ).all()
    
    return render_template('search.html',
                         query=query,
                         materials=materials,
                         departments=departments,
                         subjects=subjects)

@bp.route('/download/<int:id>')
def download_material(id):
    material = Material.query.get_or_404(id)
    
    # Increment download count
    material.download_count += 1
    from app import db
    db.session.commit()
    
    # Get file path
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename)
    
    if not os.path.exists(file_path):
        flash('File not found.', 'danger')
        return redirect(url_for('main.materials'))
    
    return send_file(file_path, as_attachment=True, download_name=material.filename)

@bp.route('/subject/<int:id>')
def subject(id):
    subject = Subject.query.get_or_404(id)
    materials = Material.query.filter(Material.subject_id == id).order_by(desc(Material.upload_date)).all()
    
    return render_template('subject.html', subject=subject, materials=materials) 