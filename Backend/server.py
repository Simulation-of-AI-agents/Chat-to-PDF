from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField
from werkzeug.utils import secure_filename
import os

# Flask-Anwendung initialisieren
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'Backend/static/css/files'

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
    
    # Dateiupload
    if request.method == 'POST' and 'file' in request.files:
        if upload_form.validate_on_submit():
            file = upload_form.file.data
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('home'))
    
    # Suche nach Dateien
    files = []
    if request.method == 'POST' and 'query' in request.form:
        query = search_form.query.data.strip().lower()
        file_list = os.listdir(app.config['UPLOAD_FOLDER'])
        files = [file for file in file_list if query in file.lower()]
        
    return render_template('index.html', upload_form=upload_form, search_form=search_form, files=files)

# Funktion zum Herunterladen von Dateien
@app.route('/files/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Hauptfunktion zum Starten der Anwendung
if __name__ == '__main__':
    app.run(debug=True)
