# Data Management Service

Enterprise-grade **Data Management Microservice** for the **RADAI Platform**. This service provides centralized document storage, dataset management, versioning, and comprehensive audit logging.

## 🎯 Overview

This is a standalone Django REST Framework service that:
- ✅ Stores and manages documents in AWS S3
- ✅ Manages structured datasets with schema validation
- ✅ Maintains immutable version history
- ✅ Provides comprehensive audit logging (append-only)
- ✅ Validates JWT tokens (does NOT issue them)
- ✅ Enforces role-based access control
- ✅ Integrates with other RADAI services via REST APIs

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- AWS S3 account (for file storage)
- JWT secret key (shared with User-Management service)

### Installation

1. **Clone and navigate to the repository:**
   ```bash
   cd data-management
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration
   ```

5. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server:**
   ```bash
   python manage.py runserver
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | *Required* |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost,127.0.0.1` |
| `DB_NAME` | PostgreSQL database name | `data_management` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | *Required* |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `USE_S3` | Enable AWS S3 storage | `False` |
| `AWS_ACCESS_KEY_ID` | AWS access key | *Required if USE_S3=True* |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | *Required if USE_S3=True* |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name | *Required if USE_S3=True* |
| `JWT_SECRET_KEY` | JWT signing key (shared) | *Required* |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_ISSUER` | Expected token issuer | `user-management-service` |
| `CORS_ALLOWED_ORIGINS` | CORS allowed origins | *Required* |

### PostgreSQL Setup

```bash
# Create database
psql -U postgres
CREATE DATABASE data_management;
CREATE USER dm_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE data_management TO dm_user;
\q
```

### AWS S3 Setup

1. Create an S3 bucket
2. Configure IAM user with S3 access
3. Set bucket policy for private access
4. Update environment variables

## 📡 API Endpoints

### Health Check
- `GET /health/` - Service health status

### Documents
- `GET /api/documents/` - List documents
- `POST /api/documents/` - Upload document
- `GET /api/documents/{id}/` - Get document details
- `PUT /api/documents/{id}/` - Update document metadata
- `DELETE /api/documents/{id}/` - Soft delete document
- `POST /api/documents/{id}/download/` - Download document
- `POST /api/documents/{id}/create_version/` - Create new version
- `GET /api/documents/my_documents/` - Get user's documents

### Datasets
- `GET /api/datasets/` - List datasets
- `POST /api/datasets/` - Create dataset
- `GET /api/datasets/{id}/` - Get dataset details
- `PUT /api/datasets/{id}/` - Update dataset
- `DELETE /api/datasets/{id}/` - Soft delete dataset
- `POST /api/datasets/{id}/create_version/` - Create new version
- `GET /api/datasets/{id}/versions/` - Get all versions
- `GET /api/datasets/{id}/validate/` - Validate against schema
- `GET /api/datasets/my_datasets/` - Get user's datasets

### Versions
- `GET /api/versions/documents/` - List document versions
- `GET /api/versions/documents/{id}/` - Get specific version
- `GET /api/versions/datasets/` - List dataset versions
- `GET /api/versions/datasets/{id}/` - Get specific version
- `POST /api/versions/comparisons/compare/` - Compare versions

### Audit
- `GET /api/audit/logs/` - List audit logs (admin only)
- `GET /api/audit/logs/statistics/` - Audit statistics
- `GET /api/audit/security/` - List security events (admin only)
- `GET /api/audit/security/unresolved/` - Unresolved security events
- `GET /api/audit/usage/` - API usage logs

## 🔐 Authentication

This service **validates JWT tokens** but does **NOT issue them**. Tokens are issued by the User-Management service.

### JWT Token Structure

```json
{
  "user_id": 123,
  "role": "admin",
  "permissions": ["manage_documents", "manage_datasets"],
  "email": "user@example.com",
  "username": "username",
  "exp": 1234567890,
  "iss": "user-management-service",
  "aud": "radai-platform"
}
```

### Making Authenticated Requests

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/documents/
```

## 🏗️ Architecture

### Directory Structure

```
data-management/
├── config/              # Django configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── documents/       # Document management
│   ├── datasets/        # Dataset management
│   ├── versions/        # Version control
│   └── audit/           # Audit logging
├── common/              # Shared utilities
│   ├── authentication.py
│   ├── permissions.py
│   └── middleware.py
├── manage.py
├── requirements.txt
└── README.md
```

### Design Principles

1. **Microservice Architecture**: Standalone service with REST API integration
2. **Immutable Versioning**: All versions are read-only once created
3. **Append-Only Audit**: Audit logs cannot be modified or deleted
4. **JWT Validation**: Trusts tokens from User-Management service
5. **S3 Storage**: All files stored in AWS S3, metadata in PostgreSQL
6. **Role-Based Access**: Permissions enforced via JWT claims

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.documents
python manage.py test apps.datasets
python manage.py test apps.versions
python manage.py test apps.audit

# With coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚢 Deployment

### Railway Deployment

1. **Connect repository to Railway**
2. **Configure environment variables** in Railway dashboard
3. **Deploy**: Railway will auto-detect Django and deploy

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `SECRET_KEY` securely
- [ ] Set up PostgreSQL database
- [ ] Configure AWS S3 bucket
- [ ] Set `ALLOWED_HOSTS` correctly
- [ ] Configure CORS origins
- [ ] Set up JWT_SECRET_KEY (shared with User-Management)
- [ ] Enable HTTPS
- [ ] Set up monitoring and logging
- [ ] Configure database backups
- [ ] Set up rate limiting

### Running with Gunicorn

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

## 🔒 Security

### Implemented Security Features

- ✅ JWT token validation
- ✅ Role-based access control
- ✅ CORS protection
- ✅ SQL injection protection (Django ORM)
- ✅ XSS protection
- ✅ CSRF protection
- ✅ Secure file upload validation
- ✅ Comprehensive audit logging
- ✅ Security event tracking
- ✅ Rate limiting ready

### Security Best Practices

1. **Never commit secrets** to version control
2. **Use strong SECRET_KEY** in production
3. **Enable HTTPS** in production
4. **Regularly update dependencies**
5. **Monitor audit logs** for suspicious activity
6. **Backup databases** regularly
7. **Limit file upload sizes**
8. **Validate file types**

## 📊 Database Models

### Documents
- Stores file metadata and S3 references
- Supports multiple document types
- Tracks ownership and access control

### Datasets
- Stores structured data (JSON/CSV)
- Schema validation support
- Lineage tracking

### Versions
- Immutable version snapshots
- Document and dataset versioning
- Version comparison

### Audit Logs
- Comprehensive action logging
- Security event tracking
- API usage monitoring
- Append-only (no updates/deletes)

## 🤝 Integration

### Calling from Other Services

```python
import requests

# Get JWT token from User-Management service
token = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Upload document
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    data = {
        'document_type': 'engineering_document',
        'owner_service': 'engineering',
        'metadata': '{"project": "P-123"}'
    }
    response = requests.post(
        'http://data-management-service/api/documents/',
        headers=headers,
        files=files,
        data=data
    )
    print(response.json())

# Create dataset
dataset_data = {
    'name': 'Training Data',
    'dataset_type': 'training',
    'domain': 'ai',
    'source_service': 'ml-service',
    'data': [{'feature1': 1, 'feature2': 2}],
    'schema': {...}
}
response = requests.post(
    'http://data-management-service/api/datasets/',
    headers=headers,
    json=dataset_data
)
print(response.json())
```

### Service Dependencies

- **User-Management Service**: Issues JWT tokens
- **Core Backend**: Stores business documents
- **Frontend**: Never directly calls this service (goes through Core Backend)

## 📈 Monitoring

### Health Check

```bash
curl http://localhost:8000/health/
```

### Audit Statistics

```bash
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/api/audit/logs/statistics/
```

### API Usage

```bash
curl -H "Authorization: Bearer TOKEN" \
     http://localhost:8000/api/audit/usage/statistics/
```

## 🛠️ Development

### Adding New Document Types

Edit [`config/settings.py`](config/settings.py):

```python
ALLOWED_DOCUMENT_TYPES = [
    'salary_slip',
    'engineering_document',
    'report',
    'your_new_type',  # Add here
]
```

### Adding New Permissions

Edit JWT payload to include new permissions, then check in views:

```python
from common.permissions import HasPermission

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [HasPermission]
    required_permission = 'your_new_permission'
```

## 📝 License

Proprietary - RADAI Platform

## 👥 Support

For issues and questions:
- Check documentation in `/docs`
- Review audit logs for debugging
- Contact platform team

---

**Built with ❤️ for RADAI Platform**
