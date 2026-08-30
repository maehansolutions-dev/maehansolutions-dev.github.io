# Maehan Website

This repository contains the backend and frontend for the Maehan website. It uses a Django backend connected to MongoDB, with LiteLLM for AI functionalities, and serves a single-page HTML frontend directly.

## Prerequisites

- Python 3.9+
- A running MongoDB instance (Local or MongoDB Atlas)

## Local Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/maehansolutions-dev/maehansolutions-dev.github.io.git
   cd maehansolutions-dev.github.io
   ```
   *(Note: Make sure to replace the repo link if it's different)*

2. **Create and activate a Python virtual environment (Recommended)**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate on Windows:
   venv\Scripts\activate
   
   # Activate on macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   Make sure you are in the project root directory where `requirements.txt` is located.
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   - Copy the `.env.example` file to create a new `.env` file in the root directory:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and fill in the necessary configuration details (e.g., MongoDB URI, API keys for AI functionalities).

## Launching the Site Locally

1. **Navigate to the backend directory**
   ```bash
   cd backend
   ```

2. **Run the Django development server**
   ```bash
   python manage.py runserver
   ```

3. **Access the application**
   Open your web browser and go to:
   ```
   http://127.0.0.1:8000/
   ```
   The Django server is configured to serve the `index.html` frontend directly at this root URL.

## Project Structure

- `/backend`: Contains the Django application, API endpoints (`/api/`), and configuration.
- `/index.html`: The main frontend file, served directly by Django's root URL.
- `requirements.txt`: Python dependencies.
- `.env.example`: Template for necessary environment variables.
