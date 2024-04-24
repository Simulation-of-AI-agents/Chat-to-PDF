from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField
from werkzeug.utils import secure_filename
import os
import fitz

# Flask-Anwendung initialisieren
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'Backend/static/css/files'
app.config['COVER_FOLDER'] = 'Backend/static/css/covers'

# Erstellen der Upload- und Suchformulare
class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[])
    submit = SubmitField("Upload File")

class SearchForm(FlaskForm):
    query = StringField("Search", validators=[])
    search_submit = SubmitField("Search")

# Funktion für den Dateiupload und die Hauptseite
@app.route('/', methods=['GET', 'POST'])
def home():
    upload_form = UploadFileForm()
    search_form = SearchForm()
    
    image_directory = app.config['COVER_FOLDER']
    image_files = sorted([f for f in os.listdir(image_directory) if f.endswith('.png')])[:3]
    images_to_pdfs = {img: img.replace('.png', '.pdf') for img in image_files}
    
    files = []
    if request.method == 'POST':
        if upload_form.validate_on_submit() and 'file' in request.files:
            file = upload_form.file.data
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            doc = fitz.open(file_path)
            page = doc.load_page(0)  
            pix = page.get_pixmap()
            cover_path = os.path.join(app.config['COVER_FOLDER'], os.path.splitext(filename)[0] + '.png')
            pix.save(cover_path)
            doc.close()
            
            return redirect(url_for('home'))
        
        elif search_form.validate_on_submit():
            query = search_form.query.data.lower()
            file_list = os.listdir(app.config['UPLOAD_FOLDER'])
            files = [file for file in file_list if query in file.lower() and file.endswith('.pdf')]

    return render_template('index.html', upload_form=upload_form, search_form=search_form, files=files, images_to_pdfs=images_to_pdfs)

# Route zu den einzelnen Chats
@app.route('/chat/<file_name>')
def show_pdf(file_name):
    file_path = file_name + '.pdf'
    return send_from_directory(app.config['UPLOAD_FOLDER'], file_path)

# Hauptfunktion zum Starten der Anwendung
if __name__ == '__main__':
    app.run(debug=True)
