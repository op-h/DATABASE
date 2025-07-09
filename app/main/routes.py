from flask import render_template, send_from_directory, current_app, abort, request
from sqlalchemy import or_
from app.main import bp
from app.models import Department, Subject, Material
from datetime import datetime
import os

@bp.route('/')
def index():
    query = request.args.get('q', '')
    departments = Department.query.all()
    materials = None
    
    if query:
        # Search for materials across all departments
        materials = Material.query.join(Subject).join(Department).filter(
            or_(
                Material.title.ilike(f'%{query}%'),
                Material.description.ilike(f'%{query}%'),
                Subject.name.ilike(f'%{query}%'),
                Department.name.ilike(f'%{query}%')
            )
        ).all()
    
    return render_template('main/index.html', 
                         departments=departments, 
                         materials=materials,
                         query=query,
                         now=datetime.utcnow())

@bp.route('/department/<int:id>')
def department(id):
    department = Department.query.get_or_404(id)
    query = request.args.get('q', '')
    subjects = department.subjects.all()
    materials = None
    
    if query:
        # Search for materials within this department
        materials = Material.query.join(Subject).filter(
            Subject.department_id == id,
            or_(
                Material.title.ilike(f'%{query}%'),
                Material.description.ilike(f'%{query}%'),
                Subject.name.ilike(f'%{query}%')
            )
        ).all()
    
    return render_template('main/department.html', 
                         department=department, 
                         subjects=subjects,
                         materials=materials,
                         query=query,
                         now=datetime.utcnow())

@bp.route('/subject/<int:id>')
def subject(id):
    subject = Subject.query.get_or_404(id)
    query = request.args.get('q', '')
    materials = subject.materials.all()
    
    if query:
        # Search for materials within this subject
        materials = Material.query.filter(
            Material.subject_id == id,
            or_(
                Material.title.ilike(f'%{query}%'),
                Material.description.ilike(f'%{query}%')
            )
        ).all()
    
    return render_template('main/subject.html', 
                         subject=subject, 
                         materials=materials,
                         query=query,
                         now=datetime.utcnow())

@bp.route('/material/<int:id>')
def material(id):
    material = Material.query.get_or_404(id)
    return render_template('main/material.html', material=material, now=datetime.utcnow())

@bp.route('/download/<int:id>')
def download_material(id):
    material = Material.query.get_or_404(id)
    try:
        material.increment_download_count()
        return send_from_directory(
            directory=os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER']),
            path=material.filename,
            as_attachment=True
        )
    except Exception as e:
        abort(404)

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('main/search.html', materials=None, query=None, now=datetime.utcnow())
    
    # Comprehensive search across all models
    materials = Material.query.join(Subject).join(Department).filter(
        or_(
            Material.title.ilike(f'%{query}%'),
            Material.description.ilike(f'%{query}%'),
            Subject.name.ilike(f'%{query}%'),
            Department.name.ilike(f'%{query}%')
        )
    ).all()
    
    return render_template('main/search.html', materials=materials, query=query, now=datetime.utcnow()) 