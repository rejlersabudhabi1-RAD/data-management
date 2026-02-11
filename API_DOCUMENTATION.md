# Data Management Service - API Documentation

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

All API endpoints (except `/health/`) require JWT authentication.

### Headers
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

---

## 📄 Documents API

### List Documents
**GET** `/api/documents/`

Query Parameters:
- `document_type` - Filter by document type
- `owner_service` - Filter by owning service
- `status` - Filter by status (active/archived/deleted)
- `search` - Search in filename, metadata, tags
- `ordering` - Sort by fields (e.g., `-created_at`)
- `page` - Page number
- `page_size` - Results per page

Response:
```json
{
  "count": 100,
  "next": "http://api/documents/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "filename": "document.pdf",
      "document_type": "engineering_document",
      "owner_service": "engineering",
      "file_size": 1024000,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Upload Document
**POST** `/api/documents/`

Content-Type: `multipart/form-data`

Form Data:
```
file: <file>
document_type: engineering_document
owner_service: engineering
metadata: {"project": "P-123"}
tags: ["tag1", "tag2"]
is_public: false
```

Response:
```json
{
  "id": "uuid",
  "document_type": "engineering_document",
  "filename": "document.pdf",
  "file_url": "https://s3.../document.pdf",
  "file_size": 1024000,
  "checksum": "sha256...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get Document Details
**GET** `/api/documents/{id}/`

Response:
```json
{
  "id": "uuid",
  "document_type": "engineering_document",
  "owner_service": "engineering",
  "file": "path/to/file",
  "file_url": "https://s3.../document.pdf",
  "filename": "document.pdf",
  "file_size": 1024000,
  "mime_type": "application/pdf",
  "checksum": "sha256...",
  "metadata": {"project": "P-123"},
  "tags": ["engineering", "drawing"],
  "current_version": 1,
  "is_latest": true,
  "status": "active",
  "created_by_user_id": 123,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Download Document
**POST** `/api/documents/{id}/download/`

Response:
```json
{
  "url": "https://s3.../document.pdf?signed=...",
  "filename": "document.pdf",
  "mime_type": "application/pdf",
  "file_size": 1024000
}
```

### Create Version
**POST** `/api/documents/{id}/create_version/`

Response:
```json
{
  "message": "Version created successfully",
  "version_number": 2,
  "document_id": "uuid"
}
```

### Get My Documents
**GET** `/api/documents/my_documents/`

Returns documents created by authenticated user.

---

## 📊 Datasets API

### List Datasets
**GET** `/api/datasets/`

Query Parameters:
- `dataset_type` - training/validation/test/production
- `domain` - hr/engineering/ai/finance
- `format` - json/csv/parquet
- `search` - Search in name, description
- `ordering` - Sort by fields

Response:
```json
{
  "count": 50,
  "results": [
    {
      "id": "uuid",
      "name": "Training Dataset",
      "dataset_type": "training",
      "domain": "ai",
      "format": "json",
      "row_count": 1000,
      "version": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Create Dataset
**POST** `/api/datasets/`

Request:
```json
{
  "name": "Training Dataset",
  "description": "AI training data",
  "dataset_type": "training",
  "domain": "ai",
  "source_service": "ml-service",
  "format": "json",
  "data": [
    {"feature1": 1, "feature2": 2, "label": 0},
    {"feature1": 3, "feature2": 4, "label": 1}
  ],
  "schema": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "feature1": {"type": "number"},
        "feature2": {"type": "number"},
        "label": {"type": "integer"}
      }
    }
  },
  "metadata": {"model": "v1.0"},
  "tags": ["training", "v1"]
}
```

Response:
```json
{
  "id": "uuid",
  "name": "Training Dataset",
  "dataset_type": "training",
  "domain": "ai",
  "format": "json",
  "row_count": 2,
  "column_count": 3,
  "version": 1,
  "checksum": "sha256...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get Dataset Details
**GET** `/api/datasets/{id}/`

Returns full dataset including data.

### Validate Dataset
**GET** `/api/datasets/{id}/validate/`

Response:
```json
{
  "valid": true,
  "message": "Dataset is valid according to schema"
}
```

### Create Dataset Version
**POST** `/api/datasets/{id}/create_version/`

Request:
```json
{
  "data": [
    {"feature1": 5, "feature2": 6, "label": 1}
  ]
}
```

Response:
```json
{
  "id": "new-uuid",
  "version": 2,
  "name": "Training Dataset",
  "parent_dataset": "uuid"
}
```

### Get Dataset Versions
**GET** `/api/datasets/{id}/versions/`

Response:
```json
[
  {
    "id": "uuid-v1",
    "version": 1,
    "row_count": 1000,
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": "uuid-v2",
    "version": 2,
    "row_count": 1500,
    "created_at": "2024-01-15T00:00:00Z"
  }
]
```

---

## 🔄 Versions API

### List Document Versions
**GET** `/api/versions/documents/`

Query Parameters:
- `document` - Filter by document ID
- `version_number` - Filter by version number

### Get Document Versions by Document
**GET** `/api/versions/documents/document/{document_id}/`

### List Dataset Versions
**GET** `/api/versions/datasets/`

### Compare Versions
**POST** `/api/versions/comparisons/compare/`

Request:
```json
{
  "entity_type": "document",
  "entity_id": "uuid",
  "version_from": 1,
  "version_to": 2
}
```

Response:
```json
{
  "id": 123,
  "entity_type": "document",
  "entity_id": "uuid",
  "version_from": 1,
  "version_to": 2,
  "changes": {
    "file_size_change": 1024,
    "checksum_changed": true,
    "metadata_changes": {
      "project": {
        "from": "P-123",
        "to": "P-124"
      }
    }
  },
  "summary": "file_size_change: 1024, checksum_changed: True",
  "compared_at": "2024-01-01T00:00:00Z"
}
```

---

## 📋 Audit API

**(Admin only)**

### List Audit Logs
**GET** `/api/audit/logs/`

Query Parameters:
- `user_id` - Filter by user
- `action` - CREATE/READ/UPDATE/DELETE
- `entity_type` - document/dataset
- `status` - SUCCESS/FAILURE

Response:
```json
{
  "count": 1000,
  "results": [
    {
      "id": 1,
      "user_id": 123,
      "action": "CREATE",
      "entity_type": "document",
      "entity_id": "uuid",
      "status": "SUCCESS",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Audit Statistics
**GET** `/api/audit/logs/statistics/`

Response:
```json
{
  "total_events": 10000,
  "last_24h": 150,
  "last_7d": 1000,
  "by_action": {
    "CREATE": 5000,
    "READ": 3000,
    "UPDATE": 1500,
    "DELETE": 500
  },
  "top_users": [
    {"user_id": 123, "count": 500},
    {"user_id": 456, "count": 300}
  ]
}
```

### List Security Events
**GET** `/api/audit/security/`

### Get Unresolved Security Events
**GET** `/api/audit/security/unresolved/`

### API Usage Statistics
**GET** `/api/audit/usage/statistics/`

---

## ❌ Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid data format"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

---

## 📝 Rate Limiting

- **Default**: 1000 requests per hour per user
- **Burst**: 100 requests per minute
- Headers returned:
  - `X-RateLimit-Limit`: Rate limit ceiling
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Reset time (Unix timestamp)

---

## 🔐 Permissions

### Permission Levels

1. **Authenticated User**
   - Read own documents/datasets
   - Create documents/datasets
   - Update own documents/datasets

2. **Admin**
   - Full access to all resources
   - View audit logs
   - Manage security events

3. **Custom Permissions**
   - `manage_documents` - Full document management
   - `manage_datasets` - Full dataset management
   - `view_audit_logs` - View audit logs

---

## 📦 Pagination

All list endpoints support pagination:

Request:
```
GET /api/documents/?page=2&page_size=20
```

Response:
```json
{
  "count": 100,
  "next": "http://api/documents/?page=3",
  "previous": "http://api/documents/?page=1",
  "results": [...]
}
```

---

## 🔍 Filtering & Search

### Search
```
GET /api/documents/?search=project
```

### Filter
```
GET /api/documents/?document_type=report&status=active
```

### Ordering
```
GET /api/documents/?ordering=-created_at
```

---

## 📊 Response Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Success (no content)
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
