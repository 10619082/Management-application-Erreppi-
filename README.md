# Flask Web App - Management of Workers
This is a web app developed with Flask for managing workers, projects (cantieri), and photo of receipts for the purchase of construction materials. It includes Firebase-based authentication, worker task management, photo management, and Excel report generation. The app uses Firebase Realtime Database and Firebase Storage to handle and store data related to workers, projects, and work activities.

## Key Features

1. **Firebase Authentication**: 
   - Login and session management using Firebase Authentication.
   
2. **Worker Management**:
   - Create new workers and assign them a specific role.
   - Delete workers with automatic handling of accounts in Firebase Authentication.
   - View all workers in the system.

3. **Construction site Management**:
   - Create and delete Construction site.
   - Handle Construction site names by replacing unsupported characters for Firebase.

4. **Photo of the purchased materials Management**:
   - View and download photos of receipts for the purchase of construction materials captured for specific periods.
   - Create ZIP files containing photos taken during a specified time frame.

5. **Task Management**:
   - Record workers' activities, including project, work description, hours worked, etc.
   - Edit and delete previously recorded activities.

6. **Excel Report Generation**:
   - Generate Excel reports for accounting, detailed activity reports, and payrolls.

7. **Worker Performance Charts**:
   - Display charts showing the number of photo of the purchased materials taken each month using Plotly.
   - Bar charts are labeled with Italian month names, and the Y-axis displays "Photo Count".

## System Requirements

Before running the app, ensure you have the following:

- Python 3.x
- Flask
- Firebase Admin SDK
- Plotly
- XlsxWriter
- dotenv

- Python 3.x
- Flask
- Firebase Admin SDK
- Plotly
- XlsxWriter
- dotenv
