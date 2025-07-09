import os
import mimetypes
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from app import db
from app.admin import bp
from app.admin.forms import DepartmentForm, SubjectForm, MaterialForm
from app.models import Department, Subject, Material
from functools import wraps
from app.admin.decorators import admin_required
from datetime import datetime

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def validate_file_type(file_path, original_filename):
    # Initialize mimetypes
    mimetypes.init()
    
    # Get the MIME type based on file extension
    file_type, _ = mimetypes.guess_type(original_filename)
    if not file_type:
        return False, "Could not determine file type"
    
    allowed_types = {
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
        'text/plain': '.txt',
        'image/jpeg': '.jpg',
        'image/png': '.png'
    }
    
    if file_type not in allowed_types:
        return False, f"Invalid file type: {file_type}"
    
    extension = os.path.splitext(original_filename)[1].lower()
    if extension != allowed_types[file_type]:
        return False, "File extension does not match its content type"
    
    return True, None

@bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/index.html', now=datetime.utcnow())

# Department management
@bp.route('/departments')
@login_required
@admin_required
def departments():
    query = request.args.get('q', '')
    if query:
        departments = Department.query.filter(
            Department.name.ilike(f'%{query}%')
        ).all()
    else:
        departments = Department.query.all()
    return render_template('admin/departments.html', departments=departments, now=datetime.utcnow())

@bp.route('/department/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        department = Department()
        department.name = form.name.data
        db.session.add(department)
        db.session.commit()
        flash('Department added successfully!', 'success')
        return redirect(url_for('admin.departments'))
    return render_template('admin/department_form.html', form=form, title='New Department', now=datetime.utcnow())

@bp.route('/department/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_department(id):
    department = Department.query.get_or_404(id)
    form = DepartmentForm(obj=department)
    if form.validate_on_submit():
        department.name = form.name.data
        db.session.commit()
        flash('Department updated successfully!', 'success')
        return redirect(url_for('admin.departments'))
    return render_template('admin/department_form.html', form=form, title='Edit Department', now=datetime.utcnow())

# Subject management
@bp.route('/subjects')
@login_required
@admin_required
def subjects():
    query = request.args.get('q', '')
    if query:
        subjects = Subject.query.join(Department).filter(
            or_(
                Subject.name.ilike(f'%{query}%'),
                Department.name.ilike(f'%{query}%')
            )
        ).all()
    else:
        subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects, now=datetime.utcnow())

@bp.route('/subject/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_subject():
    form = SubjectForm()
    if form.validate_on_submit():
        subject = Subject()
        subject.name = form.name.data
        subject.department_id = form.department_id.data
        db.session.add(subject)
        db.session.commit()
        flash('Subject added successfully!', 'success')
        return redirect(url_for('admin.subjects'))
    return render_template('admin/subject_form.html', form=form, title='New Subject', now=datetime.utcnow())

@bp.route('/subject/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_subject(id):
    subject = Subject.query.get_or_404(id)
    form = SubjectForm(obj=subject)
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.department_id = form.department_id.data
        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('admin.subjects'))
    return render_template('admin/subject_form.html', form=form, title='Edit Subject', now=datetime.utcnow())

# Material management
@bp.route('/materials')
@login_required
@admin_required
def materials():
    query = request.args.get('q', '')
    if query:
        materials = Material.query.join(Subject).join(Department).filter(
            or_(
                Material.title.ilike(f'%{query}%'),
                Material.description.ilike(f'%{query}%'),
                Subject.name.ilike(f'%{query}%'),
                Department.name.ilike(f'%{query}%')
            )
        ).all()
    else:
        materials = Material.query.all()
    return render_template('admin/materials.html', materials=materials, now=datetime.utcnow())

@bp.route('/material/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_material():
    form = MaterialForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(os.path.join(current_app.root_path, file_path))
        
        material = Material()
        material.title = form.title.data
        material.description = form.description.data
        material.filename = filename
        material.file_type = filename.rsplit('.', 1)[1].lower()
        material.file_size = os.path.getsize(os.path.join(current_app.root_path, file_path))
        material.subject_id = form.subject_id.data
        material.uploaded_by = current_user.id
        
        db.session.add(material)
        db.session.commit()
        flash('Material added successfully!', 'success')
        return redirect(url_for('admin.materials'))
    return render_template('admin/material_form.html', form=form, title='New Material', now=datetime.utcnow())

@bp.route('/material/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_material(id):
    material = Material.query.get_or_404(id)
    form = MaterialForm(obj=material)
    if form.validate_on_submit():
        if form.file.data:
            # Delete old file
            old_file_path = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], material.filename)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
            
            # Save new file
            file = form.file.data
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(os.path.join(current_app.root_path, file_path))
            
            material.filename = filename
            material.file_type = filename.rsplit('.', 1)[1].lower()
            material.file_size = os.path.getsize(os.path.join(current_app.root_path, file_path))
        
        material.title = form.title.data
        material.description = form.description.data
        material.subject_id = form.subject_id.data
        db.session.commit()
        flash('Material updated successfully!', 'success')
        return redirect(url_for('admin.materials'))
    return render_template('admin/material_form.html', form=form, title='Edit Material', now=datetime.utcnow()) 

@bp.route('/material/<int:id>/delete')
@login_required
@admin_required
def delete_material(id):
    material = Material.query.get_or_404(id)
    
    # Delete the file from storage
    file_path = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], material.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete the database record
    db.session.delete(material)
    db.session.commit()
    
    flash('Material deleted successfully!', 'success')
    return redirect(url_for('admin.materials')) 

@bp.route('/department/<int:id>/delete')
@login_required
@admin_required
def delete_department(id):
    department = Department.query.get_or_404(id)
    
    # Check if department has any subjects
    if department.subjects.count() > 0:
        flash('Cannot delete department that contains subjects. Please delete all subjects first.', 'danger')
        return redirect(url_for('admin.departments'))
    
    db.session.delete(department)
    db.session.commit()
    flash('Department deleted successfully!', 'success')
    return redirect(url_for('admin.departments'))

@bp.route('/subject/<int:id>/delete')
@login_required
@admin_required
def delete_subject(id):
    subject = Subject.query.get_or_404(id)
    
    # Check if subject has any materials
    if subject.materials.count() > 0:
        flash('Cannot delete subject that contains materials. Please delete all materials first.', 'danger')
        return redirect(url_for('admin.subjects'))
    
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('admin.subjects')) 