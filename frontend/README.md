# frontend

## Project setup

### 1. Clone the repository
```bash
git clone <repository-url>
cd UI_GRC
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install backend dependencies (if requirements.txt exists)
pip install -r requirements.txt

# Run backend server
cd backend
python manage.py runserver
```

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run serve
```

### 4. Environment Configuration
```bash
# Create .env file from the provided .env.text
# Copy the .env.text content and create a .env file in the frontend directory
# Example:
# VUE_APP_API_URL=http://localhost:8000
# VUE_APP_S3_URL=http://13.233.147.73
# Add other environment variables as needed
```

## Deployment Information

### Frontend Deployment
- **Deployment Folder**: `DIST`
- **Deployed URL**: http://13.234.202.207
- **EC2 Instance Name**: RISKAVAIRE_FRONTEND

### Backend Deployment
- **Deployment Type**: Docker Image
- **EC2 Instance Name**: GRC-App-Server

### S3 Microservice Deployment
- **EC2 Instance Name**: grcdemo_microservice
- **Deployed URL**: http://13.233.147.73

