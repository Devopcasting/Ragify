import os
import shutil
import hashlib
from flask import Blueprint, render_template, flash, redirect, request, url_for
from werkzeug.utils import secure_filename
from app import app, db
from app.upload.forms import UploadForm
from app.models import Document
from app.upload.doc_pdf.embedding import ProcessPDFDcoument

# Create a Blueprint instance for the 'upload' module
upload_route = Blueprint('upload', __name__, template_folder='templates')

# Determine the configuration to use based on an environment variable
config_name = os.getenv('FLASK_CONFIG', 'development')

# File upload path
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'documents')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Vector database path
VECTOR_DB_PATH = os.path.join(app.root_path, 'static', 'vectordb')
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

# Allowed Extentions
# The supported file types are PDF, MD, TXT, DOCX, HTML, CSV, XLS, and XLSX.
ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'docx', 'html', 'csv', 'xls', 'xlsx'}
ALLOWED_EXTENSIONS_STR = ", ".join(ALLOWED_EXTENSIONS)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file types
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Get the file size
def get_pdf_file_size(file_path) -> str:
    # Get the file size in bytes
    size_bytes = os.path.getsize(file_path)
    # Determine the appropriate unit (KB or MB) based on file size
    if size_bytes < 1024:
        file_size = f'{size_bytes} bytes'
    elif size_bytes < 1024 * 1024:
        file_size = f'{size_bytes / 1024:.2f} KB'
    else:
        file_size = f'{size_bytes / (1024 * 1024):.2f} MB'

    return file_size

# Identify the document type
def identify_document_type(file_path) -> str:
    # Use the file extension to identify the document type
    file_extension = os.path.splitext(file_path)[1][1:].lower()
    if file_extension == 'pdf':
        return 'PDF'
    elif file_extension in ['md', 'txt', 'docx', 'html', 'csv', 'xls', 'xlsx']:
        return 'Text'
    else:
        return 'Unknown'
    
# Add a route for the upload page
@upload_route.route('/upload', methods=['GET', 'POST'])
def upload():
    # Pagination
    page = request.args.get('page', 1, type=int)
    # Total documents uploaded
    total_documents = Document.query.count()
    # Documents per page
    documents_per_page = 5
    # Get the documents for the current page
    documents = Document.query.order_by(Document.id.desc()).paginate(page=page, per_page=documents_per_page, error_out=False)

    form = UploadForm()
    if form.validate_on_submit():
        # Get the uploaded file from the form
        file = request.files['file']
        file_name = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        
        if file and allowed_file(file_name):
            # Check if the md5sum of the file is already available in the database
            md5sum = hashlib.md5(file.read()).hexdigest()
            file.seek(0)
            document = Document.query.filter_by(md5sum=md5sum).first()
            if document:
                flash(f"Document already exists! '{file_name}'", 'danger')
                return redirect(request.url)
            # Save the file to the upload folder
            file.save(file_path)

            # Identify the document type
            document_type = identify_document_type(file_path)
            # Case for document type
            match document_type:
                case 'PDF':
                    # Process the PDF document
                    process_pdf = ProcessPDFDcoument(file_path, VECTOR_DB_PATH)
                    if not process_pdf.embed_doc():
                        flash(f"Failed to process PDF document! '{file_name}'", 'danger')
                        return redirect(request.url)
            # Get the document size
            document_size = get_pdf_file_size(file_path)
           
            # Create a new Document instance and add it to the database
            document = Document(name=file_name, size=document_size, path=file_path, md5sum=md5sum)
            db.session.add(document)
            db.session.commit()

            # Redirect to the home page after successful upload
            flash(f"Document uploaded successfully! '{file_name}'", 'success')
            return redirect(url_for('upload.upload'))
        else:
            flash(f"Document type not allowed! '{file_name}'", 'danger')
            return redirect(request.url)
    return render_template('upload/upload.html', title='Upload', form=form, documents=documents, total_documents=total_documents)