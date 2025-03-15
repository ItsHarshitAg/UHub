from werkzeug.utils import secure_filename
import os
from flask import current_app

def allowed_file(filename):
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'png', 'jpg', 'jpeg'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, upload_folder=None):
    """Save an uploaded file and return the path"""
    if not file or not allowed_file(file.filename):
        return None
    
    if upload_folder is None:
        upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # Ensure the upload folder exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Secure the filename and save the file
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    # Return a relative path for database storage
    return os.path.join('uploads', filename)
