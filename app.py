from flask import Flask, render_template, redirect, url_for, send_from_directory, flash, request , jsonify
import firebase_admin
from firebase_admin import credentials, storage, firestore, db
from datetime import datetime, timedelta
import os
import io
import zipfile
import logging
import openpyxl  # Libreria per gestire Excel
from dotenv import load_dotenv
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

# Carica le variabili d'ambiente dal file .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  

app.debug = False

# Inizializza il logger
logging.basicConfig(level=logging.DEBUG if app.debug else logging.INFO)

# Inizializza Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv('FIREBASE_KEY_PATH'))
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
        'databaseURL': os.getenv('FIREBASE_DB_URL')  # Aggiungi l'URL del database in tempo reale
    })

bucket = storage.bucket()
db_ref = db.reference("/Attivita/Utenti")

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

@app.route('/gestione_excel', methods=['GET', 'POST'])
def gestione_excel():
    if request.method == 'POST':
        data_inizio = request.form.get('data_inizio')
        data_fine = request.form.get('data_fine')

        # Validazione delle date
        if not data_inizio or not data_fine:
            flash("Per favore, seleziona entrambe le date.")
            return redirect(url_for('gestione_excel'))

        # Fetch dei dati da Firebase
        attivita_list = fetch_attivita_from_firebase(data_inizio, data_fine)

        if not attivita_list:
            flash("Nessuna attività trovata per il periodo selezionato.")
            return redirect(url_for('gestione_excel'))

        # Genera il file Excel
        excel_filename = generate_excel(attivita_list, data_inizio, data_fine)

        # Fornisci il file Excel per il download
        return send_from_directory(TEMP_DIR, excel_filename, as_attachment=True)

    return render_template('gestione_excel.html')

def fetch_attivita_from_firebase(data_inizio, data_fine):
    # Converti le date in oggetti datetime
    data_inizio_dt = datetime.strptime(data_inizio, "%Y-%m-%d")
    data_fine_dt = datetime.strptime(data_fine, "%Y-%m-%d")
    
    attivita_list = []
    
    # Leggi i dati da Firebase Realtime Database
    snapshot = db_ref.get()

    # Itera attraverso gli utenti e le attività
    for user, attivita_data in snapshot.items():
        for attivita_id, attivita in attivita_data.items():
            # Confronta le date delle attività con il range specificato
            attivita_data_str = attivita.get('data')
            if attivita_data_str:
                attivita_data_dt = datetime.strptime(attivita_data_str, "%d/%m/%Y")

                if data_inizio_dt <= attivita_data_dt <= data_fine_dt:
                    attivita_list.append({
                        'data': attivita.get('data'),
                        'cantiere': attivita.get('cantiere'),
                        'operaio': attivita.get('operaio'),
                        'ore': attivita.get('ore'),
                        'lavorazione': attivita.get('lavorazione'),
                        'pioggia_vento': attivita.get('pioggia_vento', ''),
                        'ferie_permesso': attivita.get('ferie_permesso', '')
                    })
    return attivita_list

def generate_excel(attivita_list, data_inizio, data_fine):
    filename = f"Foglio_Excel_{data_inizio}_to_{data_fine}.xlsx"
    filepath = os.path.join(TEMP_DIR, filename)

    # Crea il workbook Excel
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Attività"

    # Crea intestazioni
    headers = ["Data", "Cantiere", "Operaio", "Ore", "Lavorazione", "Pioggia/Vento", "Ferie/Permesso"]
    sheet.append(headers)

    # Stili per le celle
    header_font = Font(bold=True)
    alignment = Alignment(horizontal="center")

    for col_num, header in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col_num)
        cell.font = header_font
        cell.alignment = alignment

    # Inserisci i dati delle attività
    for attivita in attivita_list:
        row = [
            attivita['data'],
            attivita['cantiere'],
            attivita['operaio'],
            attivita['ore'],
            attivita['lavorazione'],
            attivita['pioggia_vento'],
            attivita['ferie_permesso']
        ]
        sheet.append(row)

    # Imposta la larghezza delle colonne
    for col in sheet.columns:
        max_length = max(len(str(cell.value)) for cell in col)
        adjusted_width = (max_length + 2)
        sheet.column_dimensions[get_column_letter(col[0].column)].width = adjusted_width

    # Salva il file Excel
    workbook.save(filepath)

    return filename

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

        logging.debug(f"Start Year: {start_year}, Start Month: {start_month}, End Year: {end_year}, End Month: {end_month}")

        action = request.form.get('action')  # Visualizza o Scarica
        
        # Imposta il periodo da visualizzare accanto a "Risultati"
        if end_year == '':
            period = f"{start_month}/{start_year}"
        else:
            period = f"da {start_month}/{start_year} a {end_month}/{end_year}"

        if action == "Visualizza Foto":
            logging.debug(f"Azione selezionata: {action}")
            photo_urls = fetch_photos(start_year, start_month, end_year, end_month)
            logging.debug(f"Numero di foto trovate: {len(photo_urls)}")
            return render_template('gestione_foto_bolle.html', photo_urls=photo_urls, years=years, months=months, period=period)
        
        elif action == "Scarica Foto":
            logging.debug(f"Azione selezionata: {action}")
            zip_filepath = create_zip(start_year, start_month, end_year, end_month)
            
            if zip_filepath is None:
                logging.debug("Nessuna foto trovata per il periodo selezionato")
                return jsonify({'error': 'Non ci sono foto per il periodo selezionato.'})
            else:
                logging.debug(f"File ZIP creato: {zip_filepath}")
                zip_url = url_for('download_zip', filename=os.path.basename(zip_filepath))
                return jsonify({'zip_url': zip_url})
            
    return render_template('gestione_foto_bolle.html', years=years, months=months, period=period)

def fetch_photos(start_year, start_month, end_year, end_month):
    start_year = int(start_year)
    start_month = int(start_month)
    photo_urls = []

    logging.debug(f"Fetching photos from {start_month}/{start_year} to {end_month}/{end_year}")

    # Se l'utente non seleziona la data di fine
    if end_year =='':
        blobs = list(bucket.list_blobs(prefix=f"DDT/{start_year}/{start_month}/"))
        logging.debug(f"Numero di blob trovati per {start_month}/{start_year}: {len(blobs)}")
        for blob in blobs:
            url = blob.generate_signed_url(timedelta(seconds=300), method='GET')
            photo_urls.append(url)
    else:
        # Logica per iterare tra più anni e mesi
        
        end_year = int(end_year)
        end_month = int(end_month)

        for year in range(start_year, end_year + 1):
            month_start = start_month if year == start_year else 1
            month_end = end_month if year == end_year else 12

            for month in range(month_start, month_end + 1):
                logging.debug(f"Fetching blobs for {month}/{year}")
                blobs = list(bucket.list_blobs(prefix=f"DDT/{year}/{month}/"))
                logging.debug(f"Numero di blob trovati per {month}/{year}: {len(blobs)}")
                for blob in blobs:
                    logging.debug(f"Blob trovato: {blob.name}")
                    url = blob.generate_signed_url(timedelta(seconds=300), method='GET')
                    photo_urls.append(url)
                    
    return photo_urls

def create_zip(start_year, start_month, end_year, end_month):
    start_year = int(start_year)
    start_month = int(start_month)

    no_photos = True  # Flag per tenere traccia se ci sono foto o meno

    if end_year == '':
        zip_filename = f"foto_{start_year}_{start_month}.zip"
        end_year = start_year
        end_month = start_month
    else:
        end_year = int(end_year)
        end_month = int(end_month)
        # Crea un file ZIP temporaneo per il range di date
        zip_filename = f"foto_{start_year}_{start_month}_to_{end_year}_{end_month}.zip"

    zip_filepath = os.path.join(TEMP_DIR, zip_filename)

    logging.debug(f"Creazione del file ZIP: {zip_filename}")

    # Apri il file ZIP
    with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Itera su tutti gli anni e mesi tra la data di inizio e di fine
        for year in range(start_year, end_year + 1):
            # Definisci il mese di inizio e di fine per ciascun anno
            month_start = start_month if year == start_year else 1
            month_end = end_month if year == end_year else 12

            for month in range(int(month_start), month_end + 1):
                # Ottieni i blob per l'anno e il mese correnti
                logging.debug(f"Elaborazione blobs per {month}/{year}")
                blobs = list(bucket.list_blobs(prefix=f"DDT/{year}/{month}/"))

                if len(blobs) == 0:
                    logging.debug(f"Nessun blob trovato per {month}/{year}")
                    continue  # Nessun blob per questo mese, continua con il prossimo

                no_photos = False  # Se troviamo almeno un blob, imposta no_photos a False

                for idx, blob in enumerate(blobs):
                    blob_name = blob.name
                    blob_name = '/'.join(blob_name.split('/')[1:])  # Rimuove il prefisso 'DDT'

                    logging.debug(f"Aggiunta al file ZIP: {blob_name}")

                    if blob.exists():  # Verifica che il blob esista
                        image_data = blob.download_as_bytes()  # Scarica i dati del blob
                        zip_file.writestr(f"{blob_name}", image_data)  # Salva l'immagine nel file ZIP
                    else:
                        logging.debug(f"Errore: Blob {blob_name} non trovato")

    # Se no_photos è True, significa che non ci sono foto, elimina lo zip
    if no_photos:
        logging.debug("Nessuna foto trovata, elimino il file ZIP vuoto.")
        os.remove(zip_filepath)  # Rimuovi il file ZIP che è stato creato vuoto
        return None

    logging.debug(f"File ZIP creato con successo: {zip_filepath}")
    return zip_filename

@app.route('/download_zip/<filename>')
def download_zip(filename):
    return send_from_directory(TEMP_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
