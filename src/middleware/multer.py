import os
import time
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'public/uploads'
ALLOWED_EXTENSIONS = {'jpeg', 'jpg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limit

def allowed_file(filename):
    # only images
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def save_uploaded_file(file, subfolder=''):
    # unique name
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        raise ValueError('Only image files are allowed!')
    
    # Check size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise ValueError('File size exceeds 5MB limit!')
    
    # create directory 
    upload_path = os.path.join(UPLOAD_FOLDER, subfolder) if subfolder else UPLOAD_FOLDER
    os.makedirs(upload_path, exist_ok=True)
    
   # uniqu name
    ext = os.path.splitext(file.filename)[1].lower()
    filename = f"{int(time.time() * 1000)}{ext}"
    
    filepath = os.path.join(upload_path, filename)
    file.save(filepath)
    
    # get path
    if subfolder:
        return f'/uploads/{subfolder}/{filename}'
    return f'/uploads/{filename}'

def get_upload_folder():
    return UPLOAD_FOLDER

def delete_uploaded_file(file_url):
    if not file_url:
        return False

    relative_path = file_url.lstrip('/')
    base_dir = os.path.dirname(UPLOAD_FOLDER.rstrip('/'))
    full_path = os.path.join(base_dir, relative_path)

    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        else:
            print(f"File not found: {full_path}")
            return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False