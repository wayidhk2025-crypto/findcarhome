# FindCarHome Gabon - Django Backend

Django REST API for file uploads with Firebase authentication.

## Quick Start

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Run development server
python manage.py runserver
```

## Environment Variables

Create a `.env` file with:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Firebase
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json

# AWS S3 (for production)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=eu-west-3
```

## API Endpoints

- `POST /api/upload/` - Upload a file
- `POST /api/upload/batch_upload/` - Upload multiple files
- `GET /api/upload/by_listing/` - Get files for a listing
- `DELETE /api/upload/<id>/` - Delete a file
- `POST /api/upload/<id>/set_primary/` - Set as primary image
