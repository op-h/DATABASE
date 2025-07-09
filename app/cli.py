import os
import click
from flask.cli import with_appcontext
from app import db
from app.models import User, Department

def register_commands(app):
    app.cli.add_command(create_admin)
    app.cli.add_command(create_departments)

@click.command('create-admin')
@with_appcontext
def create_admin():
    """Create the admin user."""
    email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    password = os.getenv('ADMIN_PASSWORD', 'change-this-password')
    
    if User.query.filter_by(email=email).first():
        click.echo('Admin user already exists.')
        return
    
    user = User(email=email, is_admin=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    click.echo(f'Created admin user with email: {email}')

@click.command('create-departments')
@with_appcontext
def create_departments():
    """Create initial departments."""
    departments = [
        {'name': 'Computer Science', 'description': 'Computer Science and Programming courses'},
        {'name': 'Mathematics', 'description': 'Mathematics and Statistics courses'},
        {'name': 'Engineering', 'description': 'Engineering and Technology courses'},
        {'name': 'Physics', 'description': 'Physics and Physical Sciences courses'}
    ]
    
    for dept_data in departments:
        if not Department.query.filter_by(name=dept_data['name']).first():
            department = Department(name=dept_data['name'], description=dept_data['description'])
            db.session.add(department)
    
    db.session.commit()
    click.echo('Created initial departments') 