# Flask Web App - Management of Workers, Projects, and Photo Bolle

This is a web app developed with Flask for managing workers, projects (cantieri), and photo bolle. It includes Firebase-based authentication, worker task management, photo bolle management, and Excel report generation. The app uses Firebase Realtime Database and Firebase Storage to handle and store data related to workers, projects, and work activities.

## Key Features

1. **Firebase Authentication**: 
   - Login and session management using Firebase Authentication.
   
2. **Worker Management**:
   - Create new workers and assign them a specific role.
   - Delete workers with automatic handling of accounts in Firebase Authentication.
   - View all workers in the system.

3. **Project Management (Cantieri)**:
   - Create and delete projects.
   - Handle project names by replacing unsupported characters for Firebase.

4. **Photo Bolle Management**:
   - View and download photo bolle captured for specific periods.
   - Create ZIP files containing photos taken during a specified time frame.

5. **Task Management**:
   - Record workers' activities, including project, work description, hours worked, etc.
   - Edit and delete previously recorded activities.

6. **Excel Report Generation**:
   - Generate Excel reports for accounting, detailed activity reports, and payrolls.

7. **Worker Performance Charts**:
   - Display charts showing the number of photo bolle taken each month using Plotly.
   - Bar charts are labeled with Italian month names, and the Y-axis displays "Photo Count".

## System Requirements

Before running the app, ensure you have the following:

- Python 3.x
- Flask
- Firebase Admin SDK
- Plotly
- XlsxWriter
- dotenv

## Installation

### Clone the repository


Create a virtual environment and install dependencies
Create a virtual environment:

python -m venv venv
Activate the virtual environment:

On macOS/Linux:

source venv/bin/activate
On Windows:

venv\Scripts\activate
Install the dependencies:


pip install -r requirements.txt
Firebase Configuration
Create a Firebase Project:

Go to Firebase Console and create a new project.
Enable Firebase Authentication (Email/Password) and Firebase Realtime Database.
Download Firebase Admin SDK credentials:

After setting up the project, download the Firebase Admin SDK credentials file (serviceAccountKey.json).
Set up environment variables:

Create a .env file in the root of the project and add the following keys:

SECRET_KEY="your_secret_key"
FIREBASE_KEY_JSON='{"type": "service_account", "project_id": "...", ...}'  # Content of the Firebase credentials JSON
FIREBASE_STORAGE_BUCKET="your-bucket-name.appspot.com"
FIREBASE_DB_URL="https://your-project.firebaseio.com/"
USER_NAME="your_username"
USER_PASSWORD="your_password"
Running the App
Run the app:

flask run
Visit http://127.0.0.1:5000/ in your browser and log in with the credentials set in the .env file.

Project Structure

Copia codice
├── app.py                         # Main Flask app file
├── templates/                     # HTML templates for rendering pages
│   ├── login.html                 # Login page
│   ├── index.html                 # Homepage
│   ├── gestione_cantieri.html     # Project management page
│   ├── gestione_operai.html       # Worker management page
│   ├── gestione_foto_bolle.html   # Photo bolle management page
│   ├── gestione_excel.html        # Excel report generation page
│   ├── performance_operai.html    # Worker performance chart page
│   └── ...                        # Other HTML files
├── static/                        # Static files (CSS, JS, images)
├── .env                           # Configuration file with environment variables
├── requirements.txt               # Python dependencies for the app
├── README.md                      # Documentation of the app
└── ...                            # Other files and directories
Using the App
Login
Log in using the credentials defined in the .env file. Once logged in, you will have access to all the app's features.

Worker Management
Navigate to the "Worker Management" page to add or delete workers.
Each worker has a name, surname, hourly cost, and an email address automatically generated.
Project Management
On the "Project Management" page, you can create and remove projects.
Each project name is automatically formatted to be compatible with Firebase.
Task Management
Record new work activities for workers, including details like project, work description, and hours worked.
You can also edit or delete previously recorded activities.
Photo Bolle Management
View or download all photo bolle uploaded within a specific time frame.
Photos are stored in Firebase Storage and can be downloaded as a ZIP file.
Excel Report Generation
You can generate various Excel reports, such as accounting, detailed activity reports, and payroll for workers.
Worker Performance Charts
The chart section displays the number of photos uploaded each month, with Italian month names and the Y-axis labeled "Photo Count".
Additional Requirements
In the requirements.txt file, the dependencies necessary for the app are specified. To add Plotly, use the following version:

plotly==5.24.1
Add this version to the requirements.txt file if not already present.

Contributing
If you'd like to contribute to this project, follow these steps:

Fork the repository.
Create a branch for your feature (git checkout -b my-new-feature).
Commit your changes (git commit -am 'Add new feature').
Push the branch (git push origin my-new-feature).
Create a Pull Request.
License
This project is licensed under the MIT License - see the LICENSE file for details. """

file_path = "/mnt/data/README.md"

with open(file_path, "w") as file: file.write(content)

file_path # Return the path for user to download
