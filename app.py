from flask import Flask, render_template, redirect, url_for, send_from_directory, flash, request , jsonify
import firebase_admin
from firebase_admin import credentials, storage, firestore
from datetime import datetime, timedelta
import os
import io
import zipfile
from dotenv import load_dotenv  # Aggiungi questa riga per caricare le variabili da .env

# Carica le variabili d'ambiente dal file .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  

# Inizializza Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv('FIREBASE_KEY_PATH'))
    firebase_admin.initialize_app(cred, {'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')})

db = firestore.client()
bucket = storage.bucket()

# Directory temporanea per i file
TEMP_DIR = os.path.join(os.getcwd(), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gestione_cantieri')
def gestione_cantieri():
    return render_template('gestione_cantieri.html')

@app.route('/gestione_operai')
def gestione_operai():
    return render_template('gestione_operai.html')

@app.route('/gestione_excel')
def gestione_excel():
    return render_template('gestione_excel.html')

@app.route('/gestione_attivita')
def gestione_attivita():
    return render_template('gestione_attivita.html')

@app.route('/gestione_foto_bolle', methods=['GET', 'POST'])
def gestione_foto_bolle():
    current_year = datetime.now().year
    years = list(range(2023, current_year + 1))
    months = [f"{month:02d}" for month in range(1, 13)]
    period = ""

    if request.method == 'POST':
        start_year = request.form.get('start_year')
        start_month = request.form.get('start_month')
        end_year = request.form.get('end_year', '')
        end_month = request.form.get('end_month', '')

        action = request.form.get('action')  # Visualizza o Scarica
        
        # Imposta il periodo da visualizzare accanto a "Risultati"
        if not end_year and not end_month:
            period = f"{start_month}/{start_year}"
        else:
            period = f"da {start_month}/{start_year} a {end_month}/{end_year}"

        if action == "Visualizza Foto":
            photo_urls = fetch_photos(start_year, start_month, end_year, end_month)
            return render_template('gestione_foto_bolle.html', photo_urls=photo_urls, years=years, months=months, period=period)
        
        elif action == "Scarica Foto":
            zip_filepath = create_zip(start_year, start_month, end_year, end_month)
            zip_url = url_for('download_zip', filename=os.path.basename(zip_filepath))
            return jsonify({'zip_url': zip_url})
    
    return render_template('gestione_foto_bolle.html', years=years, months=months, period=period)


def fetch_photos(start_year, start_month, end_year, end_month):
    start_year = int(start_year)
    start_month = int(start_month)
    photo_urls = []
    # Se l'utente non seleziona la data di fine
    if not end_year and not end_month:
        blobs = list(bucket.list_blobs(prefix=f"DDT/{start_year}/{start_month}/"))
        for blob in blobs:
            url = blob.generate_signed_url(timedelta(seconds=300), method='GET')
            photo_urls.append(url)
    else:
        # Logica per iterare tra più anni e mesi
        
        end_year = int(end_year)
        end_month = int(end_month)

        print( start_year, start_month, end_year, end_month)

        for year in range(start_year, end_year + 1):
            month_start = start_month if year == start_year else 1
            month_end = end_month if year == end_year else 12

            for month in range(month_start, month_end + 1):
                blobs = list(bucket.list_blobs(prefix=f"DDT/{year}/{month}/"))
                for blob in blobs:
                    print(blob)
                    url = blob.generate_signed_url(timedelta(seconds=300), method='GET')
                    photo_urls.append(url)
                    
    return photo_urls

def create_zip(start_year, start_month, end_year, end_month):
    start_year = int(start_year)
    start_month = int(start_month)


    if not end_year and not end_month:
        zip_filename = f"foto_{start_year}_{start_month}.zip"
    else:
        end_year = int(end_year)
        end_month = int(end_month)

        # Crea un file ZIP temporaneo con tutte le foto
        zip_filename = f"foto_{start_year}_{start_month}_to_{end_year}_{end_month}.zip"
    zip_filepath = os.path.join(TEMP_DIR, zip_filename)

    with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Lista di blob dal bucket di Firebase
        blobs = bucket.list_blobs(prefix=f"DDT/{start_year}/{start_month}/")

        for idx, blob in enumerate(blobs):
            # Usa il nome del blob direttamente
            blob_name = blob.name  # Questo restituisce il percorso del blob come DDT/2024/7/Maremmana Gomme _CIVITAVECCHIA_3-7-2024 + 5c1895.jpg
            blob_name = '/'.join(blob_name.split('/')[1:])
           
            if blob.exists():  # Verifica che il blob esista
                image_data = blob.download_as_bytes()  # Scarica i dati del blob
                zip_file.writestr(f"{blob_name}", image_data)  # Salva l'immagine nel file ZIP
            else:
                print(f"Errore: Blob {blob_name} non trovato")

    return zip_filename



@app.route('/download_zip/<filename>')
def download_zip(filename):
    return send_from_directory(TEMP_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
