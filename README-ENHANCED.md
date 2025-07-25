# Enhanced PrivateGPT 🚀

An enhanced version of PrivateGPT with enterprise-grade features including Role-Based Access Control (RBAC), document-specific permissions, multi-model support, and comprehensive user management.

## 🌟 New Features

### 🔐 Authentication & Authorization
- **JWT-based authentication** with secure token management
- **Role-based access control** (SuperAdmin, Admin, User)
- **Document-specific permissions** (read, write, delete, ingest)
- **User management** with full CRUD operations

### 📄 Document Management
- **Document ownership** tracking
- **Public/private document** settings
- **Access control per document**
- **Owner-based permissions**

### 🤖 Multi-Model Support
- **Multiple LLM providers** (Ollama, OpenAI)
- **Model-specific access control**
- **Dynamic model selection** per request
- **Automatic model discovery**

### 🛡️ Security Features
- **Password hashing** with bcrypt
- **JWT token expiration**
- **Permission-based API access**
- **Database-backed user management**

## 🚀 Quick Start

### 1. Install Enhanced Dependencies

```bash
pip install -r requirements-enhanced.txt
```

### 2. Start Enhanced PrivateGPT

```bash
python enhanced_main.py
```

### 3. Default Users

The system creates default users on first startup:

| Role | Username | Password | Permissions |
|------|----------|----------|-------------|
| SuperAdmin | `superadmin` | `admin123!` | Full system access |
| Admin | `admin` | `admin123!` | User & document management |
| User | `user` | `user123!` | Basic chat & document access |

**⚠️ Change these passwords in production!**

## 📚 API Endpoints

### 🔐 Authentication

```bash
# Login
POST /v1/auth/login
{
  "username": "superadmin",
  "password": "admin123!"
}

# Get current user info
GET /v1/auth/me
Authorization: Bearer <token>

# Create user (Admin+)
POST /v1/auth/users
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "role": "user"
}
```

### 💬 Enhanced Chat

```bash
# Chat with model selection
POST /v1/chat/completions
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "model": "ollama:llama3.1",
  "use_context": true,
  "stream": false
}

# Get available models
GET /v1/chat/models
Authorization: Bearer <token>
```

### 📄 Enhanced Document Management

```bash
# Ingest document with ownership
POST /v1/ingest/file
Content-Type: multipart/form-data
Authorization: Bearer <token>

# List user's documents
GET /v1/ingest/my-documents
Authorization: Bearer <token>

# Update document visibility
PUT /v1/ingest/{doc_id}/visibility
{
  "is_public": true
}
```

### 👥 User Management (Admin+)

```bash
# List all users
GET /v1/auth/users
Authorization: Bearer <admin_token>

# Grant document access
POST /v1/auth/documents/access
{
  "user_id": 2,
  "document_id": "doc_123",
  "permissions": ["read_document", "write_document"]
}

# Grant model access
POST /v1/auth/models/access
{
  "user_id": 2,
  "model_id": 1
}
```

## 🔧 Configuration

### Enhanced Settings

Create `settings-enhanced.yaml`:

```yaml
server:
  auth:
    enabled: true
    jwt_secret: "your-super-secret-jwt-key-change-in-production"
    access_token_expire_minutes: 60
    database_url: "sqlite:///./private_gpt.db"

multi_model:
  enabled: true
  ollama_enabled: true
  ollama_base_url: "http://localhost:11434"
  openai_enabled: false
  openai_api_key: ""

rbac:
  enabled: true
  allow_public_documents: true
  default_user_can_ingest: false
  restrict_model_access: true
```

### Database Configuration

For production, use PostgreSQL:

```yaml
server:
  auth:
    database_url: "postgresql://user:password@localhost:5432/privategpt"
```

## 👤 User Roles & Permissions

### SuperAdmin
- **Full system access**
- Manage all users and roles
- Access all documents and models
- System configuration

### Admin
- **User management** (create, update, delete users)
- **Document management** (see all, manage permissions)
- **Model access management**
- View system logs

### User
- **Basic chat** functionality
- **Document ingestion** (if permitted)
- **Own document management**
- Access to assigned models

## 🤖 Model Management

### Supported Providers

#### Ollama (Local)
- Automatic model discovery
- No API key required
- Privacy-first approach

#### OpenAI
- Requires API key
- GPT-3.5, GPT-4 support
- Configurable per user

### Model Access Control

Models can be restricted per user:

```bash
# Admin grants model access
POST /v1/auth/models/access
{
  "user_id": 3,
  "model_id": 1  # Specific model ID
}
```

## 🛡️ Security Best Practices

### Production Deployment

1. **Change default passwords**
2. **Use strong JWT secret**
3. **Configure HTTPS**
4. **Use production database**
5. **Set up proper CORS**
6. **Enable authentication logs**

### Environment Variables

```bash
export PGPT_JWT_SECRET="your-production-secret"
export PGPT_DATABASE_URL="postgresql://..."
export PGPT_OPENAI_API_KEY="sk-..."
```

## 🔄 Migration from Standard PrivateGPT

The enhanced version is **backward compatible**:

1. **Original API endpoints** still work
2. **Existing documents** remain accessible
3. **Authentication is optional** (can be disabled)
4. **Gradual migration** supported

### Migration Steps

1. Install enhanced dependencies
2. Run enhanced version
3. Create users and assign permissions
4. Gradually migrate to enhanced endpoints

## 🐛 Troubleshooting

### Common Issues

#### Authentication Fails
```bash
# Check if auth is enabled
GET /health/enhanced

# Verify JWT secret is set
```

#### Model Access Denied
```bash
# Check user's model permissions
GET /v1/auth/models
```

#### Document Not Found
```bash
# Verify document ownership
GET /v1/ingest/my-documents
```

### Debug Mode

```bash
# Enable debug logging
export PGPT_LOG_LEVEL=DEBUG
python enhanced_main.py
```

## 📈 Monitoring

### Health Checks

```bash
# Enhanced health check
GET /health/enhanced

# Response includes feature status
{
  "status": "healthy",
  "features": {
    "authentication": true,
    "role_based_access": true,
    "document_ownership": true,
    "multi_model_support": true
  }
}
```

## 🤝 Contributing

Enhanced features follow the same contribution guidelines as the main project. Key areas for contribution:

- **Additional model providers**
- **Advanced permission systems**
- **Enterprise integrations**
- **Security enhancements**

## 📄 License

Same as original PrivateGPT project.

---

**🎉 Enjoy your enhanced PrivateGPT experience with enterprise-grade security and multi-model support!**
