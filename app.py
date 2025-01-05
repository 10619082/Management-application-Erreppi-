from flask import Flask, render_template, redirect, url_for, send_from_directory, flash, request , jsonify, session
import firebase_admin
from firebase_admin import credentials, storage, auth, db
from datetime import datetime, timedelta
import os
import zipfile
import logging
from dotenv import load_dotenv
import shutil
import json
import uuid
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import plotly.graph_objs as go
from collections import defaultdict
import plotly

import xlsxwriter

# Carica le variabili d'ambiente dal file .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  

firebase_key_json = os.getenv('FIREBASE_KEY_JSON')  

# Debug per verificare che il valore sia caricato correttamente
app.debug = False

# Utente e password caricati dal file .env
USER_NAME = os.getenv('USER_NAME')  # Nome utente personalizzato
USER_PASSWORD = os.getenv('USER_PASSWORD')  # Password definita nel file .env

# Inizializza il logger
logging.basicConfig(level=logging.DEBUG if app.debug else logging.INFO)

# Inizializza Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(firebase_key_json))
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
        'databaseURL': os.getenv('FIREBASE_DB_URL')  # Aggiungi l'URL del database in tempo reale
    })

bucket = storage.bucket()
db_ref = db.reference("/Attivita/Utenti")

# Directory temporanea per i file
TEMP_DIR = os.path.join(os.getcwd(), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

def clean_temp_directory():
    try:
        shutil.rmtree(TEMP_DIR)  # Rimuovi la directory temporanea e tutto il suo contenuto
        os.makedirs(TEMP_DIR, exist_ok=True)  # Ricrea la directory vuota
        logging.info("Cartella temp pulita con successo.")
    except Exception as e:
        logging.error(f"Errore durante la pulizia della cartella temp: {e}")

clean_temp_directory()


# Rotta per il login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifica se l'username e la password corrispondono a quelli nel file .env
        if username == USER_NAME and password == USER_PASSWORD:
            session['user'] = username  # Mantieni il nome utente nella sessione
            session['logged_in'] = True  # Aggiungi questa riga per settare lo stato "logged_in"
            return redirect(url_for('index'))
        else:
            flash('Credenziali non valide. Riprova.')

    return render_template('login.html')




# Rotta per l'homepage dopo il login
@app.route('/')
def index():
    if 'user' in session:
        clean_temp_directory()
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

# Rotta per il logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Sei stato disconnesso.')
    return redirect(url_for('login'))

def sostituisci_caratteri_non_ammessi(stringa):
    caratteri_non_ammessi = {'.', '$', '[', ']', '/', '#', '$', ','}
    carattere_sostitutivo = '_'
    
    for carattere in caratteri_non_ammessi:
        stringa = stringa.replace(carattere, carattere_sostitutivo)
    
    return stringa



@app.route('/gestione_cantieri', methods=['GET', 'POST'])
def gestione_cantieri():
    cantiere_ref = db.reference('Cantiere')

    if request.method == 'POST':
        azione = request.form.get('azione')  # "Inserisci" o "Elimina"
        nome_cantiere = request.form.get('nome_cantiere').strip()

        # Sostituisci caratteri non ammessi nei nomi
        nome_cantiere = sostituisci_caratteri_non_ammessi(nome_cantiere)

        if azione == 'inserisci':
            # Inserisci nuovo cantiere
            if not nome_cantiere:
                flash("Il nome del cantiere non può essere vuoto.", "danger")
            elif cantiere_ref.child(nome_cantiere).get():
                flash("Questo cantiere esiste già.", "danger")
            else:
                # Genera un ID univoco
                id_cantiere = str(uuid.uuid4())
                # Usa il nome del cantiere come chiave e assegna l'ID generato
                nuovo_cantiere_ref = cantiere_ref.child(nome_cantiere)
                nuovo_cantiere_ref.set({
                    "id": id_cantiere,  # Imposta l'ID generato
                    "nome": nome_cantiere
                })
                flash("Cantiere inserito con successo!", "success")

        elif azione == 'elimina':
            # Elimina cantiere esistente
            if not nome_cantiere:
                flash("Devi specificare il cantiere da eliminare.", "danger")
            elif not cantiere_ref.child(nome_cantiere).get():
                flash("Il cantiere da eliminare non esiste.", "danger")
            else:
                cantiere_ref.child(nome_cantiere).delete()
                flash("Cantiere eliminato con successo!", "success")

        return redirect(url_for('gestione_cantieri'))

    # Recupera l'elenco dei cantieri per mostrarli nella pagina
    cantieri = cantiere_ref.get()
    return render_template('gestione_cantieri.html', cantieri=cantieri)


@app.route('/gestione_operai', methods=['GET', 'POST'])
def gestione_operai():
    operai_ref = db.reference('Utente')

    if request.method == 'POST':
        azione = request.form.get('azione')  # Controlla se l'azione è 'inserisci' o 'elimina'

        if azione == 'inserisci':
            # Ottieni i dati dall'utente
            nome_operaio = request.form.get('nome_operaio', '').strip()
            cognome_operaio = request.form.get('cognome_operaio', '').strip()
            costo_ora_operaio = request.form.get('costo_ora_operaio', '').strip()
            password_operaio = request.form.get('password_operaio', '').strip()

            # Verifica che i campi non siano vuoti
            if not nome_operaio or not cognome_operaio or not costo_ora_operaio or not password_operaio:
                flash("Tutti i campi devono essere compilati.", "danger")
                return redirect(url_for('gestione_operai'))

            # Genera email
            email_operaio = f"{nome_operaio}{cognome_operaio}".lower() + "@mail.com"

            try:
                # Crea l'utente in Firebase Authentication
                user = auth.create_user(
                    email=email_operaio,
                    password=password_operaio,
                    display_name=f"{nome_operaio} {cognome_operaio}"
                )

                # Ottieni l'UID dell'utente creato
                uid = user.uid

                # Inserisci il nuovo operaio nel database
                operai_ref.child(nome_operaio+cognome_operaio).set({
                    "nome": nome_operaio,
                    "cognome": cognome_operaio,
                    "costoOra": costo_ora_operaio,
                    "password": password_operaio,  # Se devi memorizzare la password (opzionale, non raccomandato)
                    "email": nome_operaio+cognome_operaio,
                    "uid": uid,
                    "ruolo": "operaio"
                })

                flash("Operaio inserito con successo!", "success")
            except Exception as e:
                flash(f"Errore durante la creazione dell'utente: {str(e)}", "danger")
                return redirect(url_for('gestione_operai'))


        elif azione == 'elimina':
            # Recupera l'email dell'operaio da eliminare
            email_operaio = request.form.get('email_operaio')

            if email_operaio:
                try:
                    # Recupera l'UID dell'operaio dal database
                    operaio = operai_ref.child(email_operaio).get()
                    uid = operaio.get('uid')

                    if uid:
                        # Elimina l'utente da Firebase Authentication
                        auth.delete_user(uid)
                        flash(f"Utenza per {email_operaio} eliminata con successo da Firebase Authentication!", "success")

                    # Elimina l'operaio dal database usando l'email
                    operai_ref.child(email_operaio).delete()
                    flash(f"Operaio con email {email_operaio} eliminato con successo!", "success")
                except Exception as e:
                    flash(f"Errore durante l'eliminazione dell'utenza o dell'operaio: {str(e)}", "danger")
            else:
                flash("Errore durante l'eliminazione dell'operaio.", "danger")


        return redirect(url_for('gestione_operai'))

    # Recupera l'elenco degli operai per mostrarli nella pagina
    operai = operai_ref.get()
    return render_template('gestione_operai.html', operai=operai)


@app.route('/gestione_excel', methods=['GET', 'POST'])
def gestione_excel():

    if not session.get('logged_in'):
        flash('Devi essere autenticato per accedere a questa pagina.')
        return redirect(url_for('login'))
    
    logging.info("Accesso alla rotta gestione_excel")
    if request.method == 'POST':
        data_inizio = request.form['start_date']
        data_fine = request.form['end_date']

        # Controllo se la data di fine è precedente alla data di inizio
        if data_fine < data_inizio:
            flash("La data di fine non può essere precedente alla data di inizio.")
            return redirect(url_for('gestione_excel'))

        action = request.form['action']  # Può essere 'contabilita', 'completo', 'buste'

        logging.info(f"Data Inizio: {data_inizio}, Data Fine: {data_fine}, Azione: {action}")

        attivita_list = fetch_attivita_from_firebase(data_inizio, data_fine)

        if action == 'contabilita':
            file_path = generate_excel_contabilita(attivita_list, data_inizio, data_fine)
        elif action == 'completo':
            file_path = generate_excel_completo(attivita_list, data_inizio, data_fine)
        elif action == 'buste':
            file_path = generate_excel_buste(attivita_list, data_inizio, data_fine)

        # Restituisci il file Excel generato come risposta
        if file_path:
            return send_from_directory(TEMP_DIR, file_path, as_attachment=True)

    return render_template('gestione_excel.html')


def fetch_attivita_from_firebase(data_inizio, data_fine):
    ref = db.reference('/Attivita/Utenti')
    snapshot = ref.get()
    attivita_list = []

    for utente_id, utente_data in snapshot.items():
        for attivita_id, attivita in utente_data.items():
            data_attivita = attivita.get('data')
            if is_date_in_range(data_attivita, data_inizio, data_fine):
                attivita_list.append({
                    'data': attivita.get('data'),
                    'cantiere': attivita.get('cantiere'),
                    'operaio': attivita.get('operaio'),
                    'ore': attivita.get('ore'),
                    'lavorazione': attivita.get('lavorazione'),
                    'pioggia_vento': attivita.get('pioggia_vento'),
                    'ferie_permesso': attivita.get('ferie_permesso')
                })

    logging.info(f"Numero di attività trovate: {len(attivita_list)}")
    return attivita_list


def is_date_in_range(date_str, data_inizio, data_fine):
    # Formato della data proveniente dal database Firebase
    date_format_db = "%d/%m/%Y"
    # Formato della data proveniente dal form HTML
    date_format_form = "%Y-%m-%d"

    try:
        # Converti le date di inizio e fine provenienti dal form HTML
        data_inizio_dt = datetime.strptime(data_inizio, date_format_form)
        data_fine_dt = datetime.strptime(data_fine, date_format_form)

        # Converti la data proveniente dal database Firebase
        current_date_dt = datetime.strptime(date_str, date_format_db)

        # Verifica se la data dell'attività rientra nell'intervallo di date
        return data_inizio_dt <= current_date_dt <= data_fine_dt

    except ValueError as e:
        logging.error(f"Errore nel parsing della data: {e}")
        return False


def generate_excel_contabilita(attivita_list, inizio, fine):
    file_name = f"contabilita_{inizio}_to_{fine}.xlsx"
    file_path = os.path.join(TEMP_DIR, file_name)

    workbook = xlsxwriter.Workbook(file_path)
    worksheet = workbook.add_worksheet("Contabilità")
    
    # Definire le formattazioni
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1, 'text_wrap': True})
    number_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1, 'text_wrap': True})
    text_format = workbook.add_format({'border': 1, 'text_wrap': True})
    header_format = workbook.add_format({'bold': True, 'border': 1, 'text_wrap': True})

    # Impostare la larghezza delle colonne
    worksheet.set_column('A:A', 11)  # Colonna Data
    worksheet.set_column('B:B', 20)  # Colonna Cantiere
    worksheet.set_column('C:C', 20)  # Colonna Operaio
    worksheet.set_column('D:D', 10)  # Colonna Ore
    worksheet.set_column('E:E', 40)  # Colonna Lavorazione

    # Intestazioni
    headers = ['Data', 'Cantiere', 'Operaio', 'Ore', 'Lavorazione']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    # Scrivi i dati
    for row, attivita in enumerate(attivita_list, start=1):
        data = datetime.strptime(attivita['data'], '%d/%m/%Y')  # Convertire la data per Excel
        worksheet.write_datetime(row, 0, data, date_format)
        worksheet.write(row, 1, attivita['cantiere'], text_format)
        worksheet.write(row, 2, attivita['operaio'].split('@')[0], text_format)  # Mostra solo parte prima di '@'
        
        # Controlla se il campo 'ore' è vuoto e gestisci il caso
        ore_value = attivita['ore'] if attivita['ore'] else '0.0'
        worksheet.write_number(row, 3, float(ore_value), number_format)  # Formattare come numero con decimali
        
        worksheet.write(row, 4, attivita['lavorazione'], text_format)

    workbook.close()
    return file_name

def generate_excel_completo(attivita_list, inizio, fine):
    file_name = f"completo_{inizio}_to_{fine}.xlsx"
    file_path = os.path.join(TEMP_DIR, file_name)

    workbook = xlsxwriter.Workbook(file_path)
    worksheet = workbook.add_worksheet("Completo")

    # Definire le formattazioni
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1, 'text_wrap': True})
    number_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1, 'text_wrap': True})
    text_format = workbook.add_format({'border': 1, 'text_wrap': True})
    header_format = workbook.add_format({'bold': True, 'border': 1, 'text_wrap': True})

    # Impostare la larghezza delle colonne
    worksheet.set_column('A:A', 11)  # Colonna Data
    worksheet.set_column('B:B', 20)  # Colonna Cantiere
    worksheet.set_column('C:C', 20)  # Colonna Operaio
    worksheet.set_column('D:D', 10)  # Colonna Ore
    worksheet.set_column('E:E', 40)  # Colonna Lavorazione
    worksheet.set_column('F:F', 15)  # Colonna Pioggia/Vento
    worksheet.set_column('G:G', 15)  # Colonna Ferie/Permesso

    headers = ['Data', 'Cantiere', 'Operaio', 'Ore', 'Lavorazione', 'Pioggia_Vento', 'Ferie_Permesso']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    for row, attivita in enumerate(attivita_list, start=1):
        data = datetime.strptime(attivita['data'], '%d/%m/%Y')  # Convertire la data per Excel
        worksheet.write_datetime(row, 0, data, date_format)
        worksheet.write(row, 1, attivita['cantiere'], text_format)
        worksheet.write(row, 2, attivita['operaio'].split('@')[0], text_format)
        
        # Controlla se il campo 'ore' è vuoto e gestisci il caso
        ore_value = attivita['ore'] if attivita['ore'] else '0.0'
        worksheet.write_number(row, 3, float(ore_value), number_format)  # Formattare come numero con decimali
        
        worksheet.write(row, 4, attivita['lavorazione'], text_format)
        worksheet.write(row, 5, attivita.get('pioggia_vento', ''), text_format)
        worksheet.write(row, 6, attivita.get('ferie_permesso', ''), text_format)

    workbook.close()
    return file_name


def generate_excel_buste(attivita_list, inizio, fine):
    file_name = f"buste_paga_{inizio}_to_{fine}.xlsx"
    file_path = os.path.join(TEMP_DIR, file_name)

    workbook = xlsxwriter.Workbook(file_path)
    worksheet = workbook.add_worksheet("Buste Paga")

    # Definire le formattazioni
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1, 'text_wrap': True})
    number_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1, 'text_wrap': True})
    text_format = workbook.add_format({'border': 1, 'text_wrap': True})
    header_format = workbook.add_format({'bold': True, 'border': 1, 'text_wrap': True})

    # Impostare la larghezza delle colonne
    worksheet.set_column('A:A', 11)  # Colonna Data
    worksheet.set_column('B:B', 20)  # Colonna Cantiere
    worksheet.set_column('C:C', 20)  # Colonna Operaio
    worksheet.set_column('D:D', 10)  # Colonna Ore
    worksheet.set_column('E:E', 15)  # Colonna Pioggia/Vento
    worksheet.set_column('F:F', 15)  # Colonna Ferie/Permesso
    worksheet.set_column('G:G', 15)  # Colonna Descrizione

    headers = ['Data', 'Cantiere', 'Operaio', 'Ore', 'Pioggia_Vento', 'Ferie_Permesso','Descrizione']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    for row, attivita in enumerate(attivita_list, start=1):
        data = datetime.strptime(attivita['data'], '%d/%m/%Y')  # Convertire la data per Excel
        worksheet.write_datetime(row, 0, data, date_format)
        worksheet.write(row, 1, attivita['cantiere'], text_format)
        worksheet.write(row, 2, attivita['operaio'].split('@')[0], text_format)
        
        # Controlla se il campo 'ore' è vuoto e gestisci il caso
        ore_value = attivita['ore'] if attivita['ore'] else '0.0'
        worksheet.write_number(row, 3, float(ore_value), number_format)  # Formattare come numero con decimali
        
        worksheet.write(row, 4, attivita.get('pioggia_vento', ''), text_format)
        worksheet.write(row, 5, attivita.get('ferie_permesso', ''), text_format)
        worksheet.write(row, 6, attivita['lavorazione'], text_format)


    workbook.close()
    return file_name




@app.route('/gestione_foto_bolle', methods=['GET', 'POST'])
def gestione_foto_bolle():
    if not session.get('logged_in'):
        flash('Devi essere autenticato per accedere a questa pagina.')
        return redirect(url_for('login'))
    
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
    response = send_from_directory(TEMP_DIR, filename, as_attachment=True)
    return response


def clean_temp_directory():
    try:
        shutil.rmtree(TEMP_DIR)  # Rimuovi la directory temporanea e tutto il suo contenuto
        os.makedirs(TEMP_DIR, exist_ok=True)  # Ricrea la directory vuota
        logging.info("Cartella temp pulita con successo.")
    except Exception as e:
        logging.error(f"Errore durante la pulizia della cartella temp: {e}")


@app.route('/gestione_attivita', methods=['GET', 'POST'])
def gestione_attivita():
    if not session.get('logged_in'):
        flash('Devi essere autenticato per accedere a questa pagina.')
        return redirect(url_for('login'))

    operai_ref = db.reference('Utente')
    operai_snapshot = operai_ref.get()

    # Filtra solo gli operai (ruolo 'operaio')
    operai = {}
    if operai_snapshot:
        for email, data in operai_snapshot.items():
            if data.get('ruolo') == 'operaio':
                operai[email] = data

    return render_template('gestione_attivita.html', operai=operai)


@app.route('/nuova_attivita_operaio/<email>', methods=['GET', 'POST'])
def nuova_attivita_operaio(email):
    if not session.get('logged_in'):
        flash('Devi essere autenticato per accedere a questa pagina.')
        return redirect(url_for('login'))

    # Recupera i dati dell'operaio
    operaio_ref = db.reference('Utente').child(email.replace('.', '_').replace('@', '-'))
    operaio = operaio_ref.get()

    if request.method == 'POST':
        azione = request.form.get('azione')
        if azione == 'inserisci_complete':
            return redirect(url_for('inserisci_complete_activity', email=email))
        elif azione == 'ferie_permessi':
            return redirect(url_for('ferie_permessi_activity', email=email))
        elif azione == 'pioggia_vento':
            return redirect(url_for('pioggia_vento_activity', email=email))

    return render_template('nuova_attivita_operaio.html', operaio=operaio)

@app.route('/inserisci_complete_activity/<email>', methods=['GET', 'POST'])
def inserisci_complete_activity(email):
    if not session.get('logged_in'):
        flash('Devi essere autenticato per accedere a questa pagina.')
        return redirect(url_for('login'))

    # Recupera la lista dei cantieri
    cantiere_ref = db.reference('Cantiere')
    cantieri_snapshot = cantiere_ref.get()
    cantieri = ['Seleziona Cantiere']
    if cantieri_snapshot:
        cantieri.extend(cantieri_snapshot.keys())

    if request.method == 'POST':
        data = request.form.get('data')
        cantiere_selezionato = request.form.get('cantiere')
        ore = request.form.get('ore')
        lavorazione = request.form.get('lavorazione')

        errors = []
        if not data:
            errors.append("Seleziona una data.")
        if not cantiere_selezionato or cantiere_selezionato == 'Seleziona Cantiere':
            errors.append("Seleziona un cantiere.")
        if not ore:
            errors.append("Inserisci le ore lavorate.")
        if not lavorazione:
            errors.append("Inserisci una descrizione della lavorazione.")

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            # Converti la data al formato "giorno/mese/anno" senza zeri iniziali
            try:
                # Assumi che il formato della data sia 'YYYY-MM-DD' dall'input (puoi adattarlo al formato del form se diverso)
                parsed_data = datetime.strptime(data, '%Y-%m-%d')
                # Usa f-string per formattare manualmente la data senza zeri iniziali
                data = f"{parsed_data.day}/{parsed_data.month}/{parsed_data.year}"
            except ValueError:
                flash("Formato data non valido. Inserisci una data corretta.", 'danger')
                return redirect(url_for('inserisci_complete_activity', email=email))

            # Salva l'attività su Firebase
            
            operaio_email = email + '-mail_com'
            attivita_ref = db.reference('Attivita').child('Utenti').child(operaio_email)
            nuovo_id = attivita_ref.push().key

            attivita_data = {
                'id': nuovo_id,
                'data': data,
                'cantiere': cantiere_selezionato,
                'operaio': operaio_email,
                'ore': ore,
                'lavorazione': lavorazione,
            }

            attivita_ref.child(nuovo_id).set(attivita_data)
            flash("Attività salvata con successo!", 'success')
            return redirect(url_for('gestione_attivita'))

    return render_template('inserisci_complete_activity.html', email=email, cantieri=cantieri)


@app.route('/ferie_permessi_activity/<email>', methods=['GET', 'POST'])
def ferie_permessi_activity(email):
    if not session.get('logged_in'):
        flash('Devi essere autenticato per accedere a questa pagina.')
        return redirect(url_for('login'))

    opzioni_ferie_permesso = ['Seleziona Ferie o Permesso', 'Ferie', 'Permesso']

    if request.method == 'POST':
        data = request.form.get('data')
        ore = request.form.get('ore')
        ferie_permesso = request.form.get('ferie_permesso')

        errors = []
        if not data:
            errors.append("Seleziona una data.")
        if not ore:
            errors.append("Inserisci le ore.")
        if not ferie_permesso or ferie_permesso == 'Seleziona Ferie o Permesso':
            errors.append("Seleziona Ferie o Permesso.")

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:

            try:
                # Assumi che il formato della data sia 'YYYY-MM-DD' dall'input (puoi adattarlo al formato del form se diverso)
                parsed_data = datetime.strptime(data, '%Y-%m-%d')
                # Usa f-string per formattare manualmente la data senza zeri iniziali
                data = f"{parsed_data.day}/{parsed_data.month}/{parsed_data.year}"
            except ValueError:
                flash("Formato data non valido. Inserisci una data corretta.", 'danger')
                return redirect(url_for('inserisci_complete_activity', email=email))
            
            # Salva l'attività su Firebase
            operaio_email = email + '-mail_com'
            attivita_ref = db.reference('Attivita').child('Utenti').child(operaio_email)
            nuovo_id = attivita_ref.push().key

            attivita_data = {
                'id': nuovo_id,
                'data': data,
                'operaio': email,
                'ore': ore,
                'ferie_permesso': ferie_permesso,
            }

            attivita_ref.child(nuovo_id).set(attivita_data)
            flash("Attività salvata con successo!", 'success')
            return redirect(url_for('gestione_attivita'))

    return render_template('ferie_permessi_activity.html', email=email, opzioni=opzioni_ferie_permesso)

@app.route('/pioggia_vento_activity/<email>', methods=['GET', 'POST'])
def pioggia_vento_activity(email):
    if not session.get('logged_in'):
        flash('Devi essere autenticato per accedere a questa pagina.')
        return redirect(url_for('login'))

    opzioni_pioggia_vento = ['Seleziona Pioggia o Vento', 'Pioggia', 'Vento']

    # Recupera la lista dei cantieri
    cantiere_ref = db.reference('Cantiere')
    cantieri_snapshot = cantiere_ref.get()
    cantieri = ['Seleziona Cantiere']
    if cantieri_snapshot:
        cantieri.extend(cantieri_snapshot.keys())

    if request.method == 'POST':
        data = request.form.get('data')
        cantiere_selezionato = request.form.get('cantiere')
        ore = request.form.get('ore')
        pioggia_vento = request.form.get('pioggia_vento')

        errors = []
        if not data:
            errors.append("Seleziona una data.")
        if not cantiere_selezionato or cantiere_selezionato == 'Seleziona Cantiere':
            errors.append("Seleziona un cantiere.")
        if not ore:
            errors.append("Inserisci le ore.")
        if not pioggia_vento or pioggia_vento == 'Seleziona Pioggia o Vento':
            errors.append("Seleziona Pioggia o Vento.")

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:

            try:
                # Assumi che il formato della data sia 'YYYY-MM-DD' dall'input (puoi adattarlo al formato del form se diverso)
                parsed_data = datetime.strptime(data, '%Y-%m-%d')
                # Usa f-string per formattare manualmente la data senza zeri iniziali
                data = f"{parsed_data.day}/{parsed_data.month}/{parsed_data.year}"
            except ValueError:
                flash("Formato data non valido. Inserisci una data corretta.", 'danger')
                return redirect(url_for('inserisci_complete_activity', email=email))
            
            # Salva l'attività su Firebase
            operaio_email = email + '-mail_com'
            attivita_ref = db.reference('Attivita').child('Utenti').child(operaio_email)
            nuovo_id = attivita_ref.push().key

            attivita_data = {
                'id': nuovo_id,
                'data': data,
                'cantiere': cantiere_selezionato,
                'operaio': email,
                'ore': ore,
                'pioggia_vento': pioggia_vento,
            }

            attivita_ref.child(nuovo_id).set(attivita_data)
            flash("Attività salvata con successo!", 'success')
            return redirect(url_for('gestione_attivita'))

    return render_template('pioggia_vento_activity.html', email=email, opzioni=opzioni_pioggia_vento, cantieri=cantieri)

@app.route('/modifica_attivita/<email>', methods=['GET', 'POST'])
def modifica_attivita(email):
    if not session.get('logged_in'):
        flash('Devi essere autenticato per accedere a questa pagina.')
        return redirect(url_for('login'))

    # Sostituisci i caratteri non permessi per accedere correttamente al database
    operaio_email = email + '-mail_com'
    
    # Riferimento al database Firebase per l'utente
    attivita_ref = db.reference(f'Attivita/Utenti/{operaio_email}')
    attivita_snapshot = attivita_ref.get()

    # Lista per salvare tutte le attività
    attivita_list = []
    
    if attivita_snapshot:
        for attivita_id, attivita_data in attivita_snapshot.items():
            attivita_data['id'] = attivita_id  # Associa l'ID dell'attività ai dati
            attivita_list.append(attivita_data)  # Aggiungi l'attività alla lista

    # Funzione per convertire la data in un oggetto datetime
    def parse_date(attivita):
        try:
            return datetime.strptime(attivita['data'], '%d/%m/%Y')
        except ValueError:
            return None

    # Ordina la lista per data in ordine decrescente
    attivita_list.sort(key=parse_date, reverse=True)

    # Rendi disponibile la lista di attività nella pagina HTML
    return render_template('modifica_attivita.html', email=email, attivita_list=attivita_list)


@app.route('/edit_attivita/<email>/<attivita_id>', methods=['GET', 'POST'])
def edit_attivita(email, attivita_id):
    if not session.get('logged_in'):
        flash('Devi essere autenticato per accedere a questa pagina.')
        return redirect(url_for('login'))

    # Recupera l'attività specifica
    operaio_email = email + '-mail_com'
    attivita_ref = db.reference(f'Attivita/Utenti/{operaio_email}/{attivita_id}')
    attivita = attivita_ref.get()

    # Recupera la lista dei cantieri
    cantiere_ref = db.reference('Cantiere')
    cantieri_snapshot = cantiere_ref.get()
    cantieri = ['Seleziona Cantiere']
    if cantieri_snapshot:
        cantieri.extend(cantieri_snapshot.keys())

    # Converti la data nel formato YYYY-MM-DD solo se la data esiste
    if attivita.get('data'):
        try:
            attivita['data'] = datetime.strptime(attivita['data'], '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            flash("Errore nel formato della data salvata. Assicurati che sia DD/MM/YYYY.")

    if request.method == 'POST':
        # Aggiorna i dati dell'attività
        try:
            parsed_data = datetime.strptime(request.form['data'], '%Y-%m-%d')
            data = f"{parsed_data.day}/{parsed_data.month}/{parsed_data.year}"
        except ValueError:
            flash("Formato data non valido. Inserisci una data corretta.", 'danger')
            return redirect(url_for('edit_attivita', email=email, attivita_id=attivita_id))

        nuova_attivita = {
            'data': data,
            'cantiere': request.form['cantiere'],
            'ore': request.form['ore'],
            'lavorazione': request.form['lavorazione'],
            'pioggia_vento': request.form.get('pioggia_vento', ''),
            'ferie_permesso': request.form.get('ferie_permesso', ''),
        }
        attivita_ref.update(nuova_attivita)
        flash('Attività aggiornata con successo!')
        return redirect(url_for('modifica_attivita', email=email))

    return render_template('edit_attivita.html', email=email, attivita=attivita, cantieri=cantieri)


@app.route('/delete_attivita/<email>/<attivita_id>', methods=['POST'])
def delete_attivita(email, attivita_id):
    if not session.get('logged_in'):
        flash('Devi essere autenticato per accedere a questa pagina.')
        return redirect(url_for('login'))

    # Recupera il riferimento all'attività da eliminare
    operaio_email = email + '-mail_com'
    attivita_ref = db.reference(f'Attivita/Utenti/{operaio_email}/{attivita_id}')
    
    # Elimina l'attività
    attivita_ref.delete()
    flash('Attività eliminata con successo!')
    return redirect(url_for('modifica_attivita', email=email))



@app.route('/performance_operai', methods=['GET', 'POST'])
def performance_operai():
    # Imposta il mese e l'anno correnti come predefiniti
    oggi = datetime.today()
    mese = oggi.month
    anno = oggi.year

    if request.method == 'POST':
        # Recupera il mese e l'anno selezionati dall'utente
        mese = int(request.form.get('mese', mese))
        anno = int(request.form.get('anno', anno))

    # Calcola il primo e l'ultimo giorno del mese selezionato
    primo_giorno_mese = datetime(anno, mese, 1)
    ultimo_giorno_mese = (primo_giorno_mese + relativedelta(months=1)) - timedelta(days=1)

    # Recupera gli operai dal database
    operai_ref = db.reference('Utente')
    operai_snapshot = operai_ref.get()
    operai = {email: dati for email, dati in operai_snapshot.items() if dati.get('ruolo') == 'operaio'}

    # Recupera le attività nel mese selezionato
    attivita_ref = db.reference('Attivita/Utenti')
    attivita_snapshot = attivita_ref.get()

    # Organizza le attività per giorno e operaio
    attivita_per_operai = {}
    for operaio_email, attività_operaio in attivita_snapshot.items():
        attivita_per_giorno = {}
        for attivita_id, attivita in attività_operaio.items():
            if attivita['operaio'].split('@')[0] in operai.keys():
                data_attivita = datetime.strptime(attivita['data'], '%d/%m/%Y')
                if primo_giorno_mese <= data_attivita <= ultimo_giorno_mese:
                    giorno = data_attivita.day
                    attivita_per_giorno[giorno] = attivita
        if len(attivita_per_giorno) != 0:
            attivita_per_operai[operaio_email.split('-')[0]] = attivita_per_giorno

    # Calcola quanti giorni ci sono nel mese selezionato
    days_in_month = ultimo_giorno_mese.day

    # Calcolo delle foto per mese
    foto_per_mese = defaultdict(int)

    for month in range(1, 13):
        blobs = list(bucket.list_blobs(prefix=f"DDT/{anno}/{month}/"))
        foto_per_mese[month] = len(blobs)  # Conteggio delle foto per ogni mese

    # Creazione dell'istogramma con Plotly
    mesi_nomi = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
    fig = go.Figure([go.Bar(x=mesi_nomi, y=[foto_per_mese[mese] for mese in range(1, 13)])])

    # Aggiorna il layout del grafico per includere l'etichetta dell'asse y
    fig.update_layout(
        xaxis_title="Mesi",
        yaxis_title="Conteggio Foto",  # Asse y in italiano
        plot_bgcolor='rgba(0,0,0,0)'  # Sfondo trasparente
    )

    # Convertire il grafico in JSON per poterlo passare al template
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template(
        'performance_operai.html',
        operai=operai,
        attivita_per_operai=attivita_per_operai,
        mese=mese,
        anno=anno,
        days_in_month=days_in_month,
        mese_primo_giorno=primo_giorno_mese,
        oggi=oggi,
        graph_json=graph_json  # Passiamo l'istogramma al template
    )


if __name__ == '__main__':
    app.run(debug=True)

