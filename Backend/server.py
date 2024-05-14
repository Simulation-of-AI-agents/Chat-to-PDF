from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField
from werkzeug.utils import secure_filename
import os
import fitz  

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'Backend/static/files'
app.config['COVER_FOLDER'] = 'Backend/static/covers'

# Erstellen der Upload- und Suchformulare
class UploadFileForm(FlaskForm):
    file = FileField("File")
    submit = SubmitField("Upload File")

class SearchForm(FlaskForm):
    query = StringField("Search")
    search_submit = SubmitField("Search")

# Funktion, um Dateien nach dem letzten Modifikationszeitpunkt zu sortieren
def sort_files_by_date(directory, extension):
    full_paths = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension)]
    sorted_files = sorted(full_paths, key=os.path.getmtime, reverse=True)  # Neueste zuerst
    return [os.path.basename(f) for f in sorted_files]

@app.route('/', methods=['GET', 'POST'])
def home():
    upload_form = UploadFileForm()
    search_form = SearchForm()

    # Dies verschiebt die Definition von images_to_pdfs in den oberen Teil der Funktion,
    # sodass es immer definiert ist, unabhängig davon, welcher Codepfad ausgeführt wird.
    pdf_files = sort_files_by_date(app.config['UPLOAD_FOLDER'], '.pdf')
    images_to_pdfs = {img.replace('.pdf', '.png'): img for img in pdf_files}

    files = []
    if request.method == 'POST':
        if upload_form.validate_on_submit() and 'file' in request.files:
            file = upload_form.file.data
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Verarbeite das PDF, um ein Vorschaubild zu erstellen
            doc = fitz.open(file_path)
            page = doc.load_page(0)  # erste Seite
            pix = page.get_pixmap()
            cover_path = os.path.join(app.config['COVER_FOLDER'], os.path.splitext(filename)[0] + '.png')
            pix.save(cover_path)
            doc.close()

            return redirect(url_for('home'))

        elif search_form.validate_on_submit():
            query = search_form.query.data.lower()
            file_list = sort_files_by_date(app.config['UPLOAD_FOLDER'], '.pdf')
            files = [file for file in file_list if query in file.lower()]

            return render_template('index.html', upload_form=upload_form, search_form=search_form, files=files, images_to_pdfs=images_to_pdfs)

    # Dies stellt sicher, dass images_to_pdfs immer verfügbar ist, wenn das Template gerendert wird.
    return render_template('index.html', upload_form=upload_form, search_form=search_form, files=files, images_to_pdfs=images_to_pdfs)

@app.route('/chat/<file_name>')
def show_pdf(file_name):
    file_path = url_for('static', filename='files/' + file_name)
    return render_template('chat.html', file_path=file_path)

@app.route('/delete/<file_name>')
def delete_pdf(file_name):
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name + '.pdf')
    cover_path = os.path.join(app.config['COVER_FOLDER'], file_name + '.png')

    try:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists(cover_path):
            os.remove(cover_path)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)