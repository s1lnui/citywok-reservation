# CityWok Project - Setup Guide

### 1. Install Python
- Download Python 3.8 or higher from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

### 2. Install SQL Server
- Download SQL Server Express from Microsoft
- Install SQL Server Management Studio (SSMS) for database management

### 3. Install ODBC Driver
- Download "ODBC Driver 17 for SQL Server" from Microsoft
- This is required for Python to connect to SQL Server

## Installation Steps

### Step 1: Clone/Download Project
cd C:\Users\YourName\Desktop


### Step 2: Create Virtual Environment 
cd CityWok_Project
python -m venv venv
venv\Scripts\activate


### Step 3: Install Python Dependencies
pip install flask
pip install flask-sqlalchemy
pip install flask-login
pip install flask-mail
pip install pyodbc
pip install flask-migrate
```

Or create a `requirements.txt` file with:
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-Mail==0.9.1
pyodbc==5.0.1
Flask-Migrate==4.0.5
```

Then install all at once:
pip install -r requirements.txt

### Step 4: Configure Database

1. Open SQL Server Management Studio (SSMS)
2. Connect to your SQL Server instance
3. Create a new database named `CityWokDB`
4. Note your server name (e.g., `ERCERC-F5UPCR11` or `localhost\SQLEXPRESS`)

### Step 5: Update Configuration

Edit `config.py` and update:
```python
SQL_SERVER = 'YOUR_SERVER_NAME'  # e.g., 'localhost\SQLEXPRESS'
SQL_DATABASE = 'CityWokDB'

For email configuration (Gmail):

MAIL_USERNAME = 'your_email@gmail.com'
MAIL_PASSWORD = 'your_app_password'  

To get Gmail App Password:
1. Go to https://myaccount.google.com/apppasswords
2. Enable 2-Factor Authentication first
3. Generate a new App Password
4. Copy the 16-character password

### Step 6: Initialize Database

python init_data.py

### Step 7: Run the Application

python manage.py

The application will start on: http://localhost:5000

**Admin Account:**
- Username: `admin`
- Password: `admin123`