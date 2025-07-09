# University Course Materials Repository

A secure web application for storing and sharing university course materials. The platform provides a public interface for browsing and downloading materials, and a private admin interface for content management.

## Features

- Public interface for browsing departments, subjects, and materials
- Secure admin panel for content management
- File upload system with type validation
- Material organization by department and subject
- Responsive design using Bootstrap
- Search functionality
- Secure file handling and download system

## Requirements

- Python 3.8+
- PostgreSQL (recommended for production)
- Virtual environment (recommended)

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with the following variables:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///materials.db
   UPLOAD_FOLDER=uploads
   ```
5. Initialize the database:
   ```bash
   flask db upgrade
   ```
6. Create admin user:
   ```bash
   flask create-admin
   ```

## Running the Application

Development:
```bash
flask run
```

Production:
```bash
gunicorn run:app
```

## Security Features

- Secure file upload validation
- CSRF protection
- XSS prevention
- Secure headers
- Rate limiting
- Admin authentication

## File Type Support

Supported file types:
- PDF (.pdf)
- Microsoft Word (.docx)
- Microsoft PowerPoint (.pptx)
- Text files (.txt)
- Images (.jpg, .png)

## License

MIT License 