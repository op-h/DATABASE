import os
import click
from flask.cli import with_appcontext
from app import db
from app.models import User

def register_commands(app):
    app.cli.add_command(create_admin)

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