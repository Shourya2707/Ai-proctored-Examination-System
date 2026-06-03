# AI-Proctored Examination System

A comprehensive, real-time AI-monitored examination platform built with Django, Django Channels, and OpenCV. This system ensures academic integrity by monitoring students via webcam and browser activity during online exams.

## 🚀 Key Features

### 🤖 AI Proctoring
- **Face Detection**: Uses OpenCV to ensure the student is present throughout the exam.
- **Multiple Face Detection**: Alerts if more than one person is detected in the camera frame.
- **Looking Away Detection**: (Expandable) logic to detect if a student is frequently looking away from the screen.

### 🛡️ Anti-Cheating Measures
- **Tab Switching Detection**: Logs a violation if the student switches browser tabs.
- **Fullscreen Enforcement**: Monitors if the student exits fullscreen mode.
- **Real-time Alerts**: Immediate notifications sent to the student and admin when a violation occurs.

### 📊 Exam Management
- **Dynamic Question Creation**: Admin dashboard to create MCQ and Subjective questions.
- **Auto-Grading**: MCQs are automatically graded upon submission.
- **Violation Logging**: Detailed logs of all proctoring violations with timestamps.

### 💻 Modern Tech Stack
- **Backend**: Django 4.2+
- **Real-time**: Django Channels (WebSockets)
- **Computer Vision**: OpenCV
- **Authentication**: JWT (JSON Web Tokens)
- **Frontend**: HTML5, Vanilla CSS, JavaScript (Webcam & WebSocket integration)

---

## 🛠️ Installation & Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd ai-proctored
```

### 2. Set up Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 6. Run the Server
```bash
python manage.py runserver
```
*Note: The project uses Daphne/Channels, so it supports both HTTP and WebSockets.*

---

## 📁 Project Structure

```text
ai-proctored/
├── apps/
│   ├── users/        # User roles (Student/Admin) & Authentication
│   ├── exams/        # Exam logic, Questions, Attempts, & Grading
│   └── proctoring/   # AI Engine, WebSockets (Consumers), & Violation Logs
├── core/             # Project settings, ASGI/WSGI, & Main URLs
├── static/           # CSS, JavaScript (Proctoring logic), & Images
├── templates/        # HTML Templates (Dashboard, Exam Interface)
└── manage.py         # Django entry point
```

---

## 📖 Usage Guide

### For Admins
1. Log in to the `/admin/` or the custom Admin Dashboard.
2. Create a new Exam and add questions (MCQ or Subjective).
3. Monitor live violations as students take the exam.

### For Students
1. Log in and navigate to the Student Dashboard.
2. Select an upcoming exam and click "Start".
3. Grant camera permissions.
4. Complete the exam while remaining in fullscreen and in view of the camera.

---

## 🧪 How the AI Works
The server receives video frames via WebSockets. The `AIProctorEngine` (located in `apps/proctoring/ai_engine.py`) processes these frames using OpenCV's Haar Cascades to count faces. If a violation is found, a `ViolationLog` is created and a message is broadcast back to the student's browser.

---

## 📄 License
This project is for educational purposes and is open for further development.
