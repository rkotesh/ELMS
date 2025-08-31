# 🏫 Employee Leave Management System (ELMS)

[Live Demo on Render](https://elms-3.onrender.com)

---

## 📌 Overview
The **Employee Leave Management System (ELMS)** is a web-based platform built with **Flask** that allows organizations to manage employee leave requests, approvals, and records efficiently. It simplifies leave tracking, improves transparency, and enhances HR workflow.

---

## 🚀 Features
- 🔐 **Authentication System**
  - User Registration & Login  
  - Role-based access (Admin / Employee)

- 👨‍💼 **Employee Management**
  - Add / Edit / Delete Employee Profiles  
  - View employee details  

- 📅 **Leave Management**
  - Apply for leave  
  - Approve / Reject leave requests (Admin)  
  - Track leave history  

- 📊 **Dashboard**
  - Overview of leave statistics  
  - Pending requests, approvals, and rejections  

- 📧 **Email Notifications**
  - Password reset via **Flask-Mail**  
  - Leave application status updates  

- 🔒 **Security**
  - Password hashing with **Werkzeug**  
  - CSRF protection using **Flask-WTF**

---

## 🛠️ Tech Stack
- **Frontend:** HTML, CSS, Bootstrap  
- **Backend:** Python, Flask  
- **Database:** SQLite (can be replaced with MySQL/PostgreSQL)  
- **Authentication:** Flask-Login  
- **Email Service:** Flask-Mail  
- **Deployment:** Render  

---

## 📂 Project Structure
elms/
│── app/
│ ├── init.py # Flask app initialization
│ ├── models.py # Database models
│ ├── routes/ # Route handlers
│ │ ├── auth.py # Authentication routes
│ │ ├── employee.py # Employee management routes
│ ├── templates/ # HTML templates (Jinja2)
│ ├── static/ # CSS, JS, Images
│── migrations/ # Database migrations
│── config.py # App configuration
│── run.py # Entry point
│── requirements.txt # Dependencies
│── README.md # Documentation

yaml
Copy code

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/elms.git
cd elms
2️⃣ Create Virtual Environment & Install Dependencies
bash
Copy code
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
3️⃣ Setup Environment Variables
Create a .env file in the root directory:

env
Copy code
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_password
4️⃣ Run Database Migrations
bash
Copy code
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
5️⃣ Start the Application
bash
Copy code
python run.py
The app will run at: http://127.0.0.1:5000

🚀 Deployment on Render
Push your project to GitHub

Connect GitHub repo to Render

Add environment variables in Render Dashboard

Deploy! 🎉

👨‍💻 Author
S. Koteswararao
📧 srkotesh23@gmail.com
💼 LinkedIn - (www.linkedin.com/in/sankula-koteswararao)
🌐 Portfolio - (https://rkotesh.github.io/kotesh-portfolio/)

📜 License
This project is licensed under the MIT License – free to use and modify.
