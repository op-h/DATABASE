import os
import mimetypes
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from app import db
from app.admin import bp
from app.admin.forms import DepartmentForm, SubjectForm, MaterialForm
from app.models import Department, Subject, Material, User
from functools import wraps
from app.admin.decorators import admin_required
from datetime import datetime, timedelta

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def ensure_upload_directory():
    """Ensure the upload directory exists"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

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

@bp.before_request
def check_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('You do not have permission to access this area.', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/')
@login_required
def index():
    # Get counts for dashboard stats
    departments_count = Department.query.count()
    subjects_count = Subject.query.count()
    materials_count = Material.query.count()
    total_downloads = sum(material.download_count for material in Material.query.all())
    
    # Get recent activities (mock data for now)
    recent_activities = [
        {
            'type': 'primary',
            'action': 'Added',
            'description': 'New department: Computer Science',
            'date': datetime.utcnow() - timedelta(hours=2)
        },
        {
            'type': 'success',
            'action': 'Updated',
            'description': 'Subject: Programming Fundamentals',
            'date': datetime.utcnow() - timedelta(hours=3)
        },
        {
            'type': 'info',
            'action': 'Uploaded',
            'description': 'New material: Python Basics PDF',
            'date': datetime.utcnow() - timedelta(hours=4)
        }
    ]
    
    return render_template('admin/dashboard.html',
                         departments_count=departments_count,
                         subjects_count=subjects_count,
                         materials_count=materials_count,
                         total_downloads=total_downloads,
                         recent_activities=recent_activities)

# Department management
@bp.route('/departments')
@login_required
def departments():
    departments = Department.query.all()
    
    # Calculate material counts for each department
    for department in departments:
        department.material_count = Material.query.join(Subject).filter(Subject.department_id == department.id).count()
    
    return render_template('admin/departments.html', departments=departments)

@bp.route('/add-department', methods=['GET', 'POST'])
@login_required
def add_department():
    form = DepartmentForm()
    if form.validate_on_submit():
        department = Department(name=form.name.data, description=form.description.data)
        db.session.add(department)
        db.session.commit()
        flash('Department added successfully.', 'success')
        return redirect(url_for('admin.departments'))
    return render_template('admin/add_department.html', form=form)

@bp.route('/edit-department/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_department(id):
    department = Department.query.get_or_404(id)
    form = DepartmentForm(obj=department)
    if form.validate_on_submit():
        department.name = form.name.data
        department.description = form.description.data
        db.session.commit()
        flash('Department updated successfully.', 'success')
        return redirect(url_for('admin.departments'))
    return render_template('admin/edit_department.html', form=form, department=department)

@bp.route('/delete-department/<int:id>')
@login_required
def delete_department(id):
    department = Department.query.get_or_404(id)
    db.session.delete(department)
    db.session.commit()
    flash('Department deleted successfully.', 'success')
    return redirect(url_for('admin.departments'))

# Subject management
@bp.route('/subjects')
@login_required
def subjects():
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)

@bp.route('/add-subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    form = SubjectForm()
    form.department_id.choices = [(d.id, d.name) for d in Department.query.all()]
    if form.validate_on_submit():
        subject = Subject(name=form.name.data,
                        code=form.code.data,
                        description=form.description.data,
                        department_id=form.department_id.data)
        db.session.add(subject)
        db.session.commit()
        flash('Subject added successfully.', 'success')
        return redirect(url_for('admin.subjects'))
    return render_template('admin/add_subject.html', form=form)

@bp.route('/edit-subject/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_subject(id):
    subject = Subject.query.get_or_404(id)
    form = SubjectForm(obj=subject)
    form.department_id.choices = [(d.id, d.name) for d in Department.query.all()]
    if form.validate_on_submit():
        subject.name = form.name.data
        subject.code = form.code.data
        subject.description = form.description.data
        subject.department_id = form.department_id.data
        db.session.commit()
        flash('Subject updated successfully.', 'success')
        return redirect(url_for('admin.subjects'))
    return render_template('admin/edit_subject.html', form=form, subject=subject)

@bp.route('/delete-subject/<int:id>')
@login_required
def delete_subject(id):
    subject = Subject.query.get_or_404(id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully.', 'success')
    return redirect(url_for('admin.subjects'))

# Material management
@bp.route('/materials')
@login_required
def materials():
    materials = Material.query.all()
    return render_template('admin/materials.html', materials=materials)

@bp.route('/add-material', methods=['GET', 'POST'])
@login_required
def add_material():
    form = MaterialForm()
    if form.validate_on_submit():
        file = form.file.data
        if file and allowed_file(file.filename):
            try:
                # Ensure upload directory exists
                upload_folder = ensure_upload_directory()
                
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Get file size and type
                file_size = os.path.getsize(file_path)
                file_type = filename.rsplit('.', 1)[1].lower()
                
                material = Material(
                    title=form.title.data,
                    description=form.description.data,
                    subject_id=form.subject_id.data,
                    filename=filename,
                    file_type=file_type,
                    file_size=file_size,
                    uploaded_by=current_user.id
                )
                db.session.add(material)
                db.session.commit()
                flash('Material added successfully.', 'success')
                return redirect(url_for('admin.materials'))
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'danger')
                return render_template('admin/add_material.html', form=form)
        else:
            flash('Invalid file type. Please upload a valid file.', 'danger')
    return render_template('admin/add_material.html', form=form)

@bp.route('/edit-material/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_material(id):
    material = Material.query.get_or_404(id)
    form = MaterialForm(obj=material)
    if form.validate_on_submit():
        material.title = form.title.data
        material.description = form.description.data
        material.subject_id = form.subject_id.data
        
        # Handle file upload if a new file is provided
        if form.file.data:
            file = form.file.data
            if file and allowed_file(file.filename):
                try:
                    # Ensure upload directory exists
                    upload_folder = ensure_upload_directory()
                    
                    # Delete old file if it exists
                    old_file_path = os.path.join(upload_folder, material.filename)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                    
                    # Save new file
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    
                    # Update file metadata
                    material.filename = filename
                    material.file_type = filename.rsplit('.', 1)[1].lower()
                    material.file_size = os.path.getsize(file_path)
                except Exception as e:
                    flash(f'Error updating file: {str(e)}', 'danger')
                    return render_template('admin/edit_material.html', form=form, material=material)
            else:
                flash('Invalid file type. Please upload a valid file.', 'danger')
                return render_template('admin/edit_material.html', form=form, material=material)
        
        db.session.commit()
        flash('Material updated successfully.', 'success')
        return redirect(url_for('admin.materials'))
    return render_template('admin/edit_material.html', form=form, material=material)

@bp.route('/delete-material/<int:id>')
@login_required
def delete_material(id):
    material = Material.query.get_or_404(id)
    
    try:
        # Delete the file from disk
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], material.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        flash(f'Warning: Could not delete file from disk: {str(e)}', 'warning')
    
    # Delete the database record
    db.session.delete(material)
    db.session.commit()
    flash('Material deleted successfully.', 'success')
    return redirect(url_for('admin.materials')) 