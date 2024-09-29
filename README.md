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

"""
# Flask Web App - Worker, Project, and Photo Bolle Management

This is a web application built with Flask to manage workers, projects, and photo bolle. It includes authentication via Firebase, task management for workers, photo bolle management, and Excel report generation. The app uses Firebase Realtime Database and Firebase Storage to manage and store data related to workers, projects, and work activities.

## Key Features

1. **Firebase Authentication**: 
   - Login and session management using Firebase Authentication.
   
2. **Worker Management**:
   - Create new workers and associate them with a specific role.
   - Delete workers, with automatic management of Firebase Authentication accounts.
   - View workers in the system.

3. **Project Management**:
   - Create and remove projects.
   - Handle project names with automatic replacement of invalid characters.

4. **Photo Bolle Management**:
   - View and download photo bolle uploaded for specific time periods.
   - Create ZIP files containing the photos for a selected date range.

5. **Task Management**:
   - Record work activities for workers, including project details, hours worked, and task descriptions.
   - Modify and delete previously recorded activities.

6. **Excel Report Generation**:
   - Generate Excel reports for accounting, detailed activity logs, and worker payroll.

7. **Worker Performance Charts**:
   - View performance charts showing the number of photos uploaded per month, with labels in Italian and the Y-axis labeled as "Photo Count".

## System Requirements

Before running the app, make sure you have the following installed:

- Python 3.x
- Flask
- Firebase Admin SDK
- Plotly
- XlsxWriter
- dotenv

## Installation

### Clone the repository

```bash
git clone https://github.com/your_username/flask-webapp-worker-management](https://github.com/10619082/Management-application-Erreppi).git
cd flask-webapp-worker-management
