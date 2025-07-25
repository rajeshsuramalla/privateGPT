# Enhanced PrivateGPT Testing Guide

## 🚀 Quick Start Testing

### Prerequisites
1. Make sure you have all dependencies installed
2. Start the enhanced server
3. Test the enhanced features

### Step 1: Install Dependencies
```powershell
# Install the additional dependencies
pip install bcrypt PyJWT python-multipart SQLAlchemy alembic
```

### Step 2: Start the Enhanced Server
```powershell
# Start the enhanced PrivateGPT server
python enhanced_main.py
```

The server should start and show:
- Enhanced PrivateGPT initializing...
- Database setup complete
- Server running on http://localhost:8001

### Step 3: Test with curl Commands

#### 3.1 Health Check
```powershell
# Basic health check
curl http://localhost:8001/health

# Enhanced health check
curl http://localhost:8001/health/enhanced
```

#### 3.2 Create Default Users (First time only)
```powershell
# Create superadmin user
curl -X POST "http://localhost:8001/v1/auth/register" `
  -H "Content-Type: application/json" `
  -d '{
    "username": "superadmin",
    "email": "superadmin@example.com", 
    "password": "admin123!",
    "role": "SUPERADMIN"
  }'

# Create admin user  
curl -X POST "http://localhost:8001/v1/auth/register" `
  -H "Content-Type: application/json" `
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123!", 
    "role": "ADMIN"
  }'

# Create regular user
curl -X POST "http://localhost:8001/v1/auth/register" `
  -H "Content-Type: application/json" `
  -d '{
    "username": "user",
    "email": "user@example.com",
    "password": "user123!",
    "role": "USER"
  }'
```

#### 3.3 Login and Get Tokens
```powershell
# Login as superadmin
curl -X POST "http://localhost:8001/v1/auth/login" `
  -H "Content-Type: application/json" `
  -d '{
    "username": "superadmin",
    "password": "admin123!"
  }'

# Save the access_token from the response
# Example response: {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", "token_type": "bearer", "expires_in": 1800, "user": {...}}
```

#### 3.4 Test Protected Endpoints
```powershell
# Get current user info (replace YOUR_TOKEN with actual token)
curl -X GET "http://localhost:8001/v1/auth/me" `
  -H "Authorization: Bearer YOUR_TOKEN"

# Get available models
curl -X GET "http://localhost:8001/v1/chat/models" `
  -H "Authorization: Bearer YOUR_TOKEN"

# Test chat with model selection
curl -X POST "http://localhost:8001/v1/chat/completions" `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{
    "messages": [{"role": "user", "content": "Hello! What is 2+2?"}],
    "model": "default",
    "use_context": false,
    "stream": false
  }'
```

#### 3.5 Test Document Management
```powershell
# Ingest text with ownership
curl -X POST "http://localhost:8001/v1/ingest/text" `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{
    "file_name": "test_doc.txt",
    "text": "This is a test document for Enhanced PrivateGPT.",
    "is_public": false
  }'

# Get my documents
curl -X GET "http://localhost:8001/v1/ingest/my-documents" `
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 4: Web Interface Testing

1. Open http://localhost:8001/docs in your browser
2. You'll see the Swagger/OpenAPI documentation
3. Click "Authorize" and enter your Bearer token
4. Test endpoints directly from the web interface

### Step 5: Test Role-Based Access

#### Test Different User Roles:
1. **SuperAdmin**: Can access all endpoints, manage all users, see all documents
2. **Admin**: Can manage users, see documents they have access to
3. **User**: Can only access their own documents and basic chat

#### Test Document Access Control:
1. Create documents as different users
2. Try to access documents owned by other users
3. Test public vs private document access

### Step 6: Test Multi-Model Support

```powershell
# List available models
curl -X GET "http://localhost:8001/v1/chat/models" `
  -H "Authorization: Bearer YOUR_TOKEN"

# Chat with specific model
curl -X POST "http://localhost:8001/v1/chat/completions" `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{
    "messages": [{"role": "user", "content": "Explain quantum physics"}],
    "model": "your-model-name",
    "use_context": true
  }'
```

## 🔧 Troubleshooting

### Common Issues:

1. **Server won't start**: Check if port 8001 is available
2. **Authentication fails**: Verify user creation was successful
3. **Token expired**: Login again to get a new token
4. **Model not found**: Check available models endpoint
5. **Database errors**: Delete private_gpt_enhanced.db and restart

### Debug Commands:
```powershell
# Check server logs
# Look at the terminal where you started enhanced_main.py

# Check if database was created
ls private_gpt_enhanced.db

# Test basic endpoint without auth
curl http://localhost:8001/health
```

## 🎯 Expected Test Results

### ✅ Successful Responses:

1. **Health Check**: Should return status "ok"
2. **User Registration**: Should return user info without password
3. **Login**: Should return access_token and user details
4. **Protected Endpoints**: Should work with valid token
5. **Chat**: Should return AI responses
6. **Document Ingest**: Should create documents with ownership

### ❌ Expected Failures (Testing Access Control):

1. **Unauthorized requests**: Should return 401
2. **Accessing other users' private docs**: Should return 403
3. **Invalid tokens**: Should return 401
4. **Role restrictions**: Lower roles can't access admin endpoints

## 🎉 Next Steps

Once testing is successful:

1. **Configure your LLM models** in the settings
2. **Upload real documents** via the ingest endpoints
3. **Create additional users** with appropriate roles
4. **Test with real files** using the file upload endpoints
5. **Integrate with your existing workflow**

## 📊 Feature Summary Tested

- ✅ **Role-based access control** (SuperAdmin, Admin, User)
- ✅ **Document-specific access control** (ownership, public/private)
- ✅ **JWT authentication** with token expiration
- ✅ **Multi-model support** (model selection in chat)
- ✅ **Enhanced API endpoints** with proper authorization
- ✅ **Backward compatibility** with original PrivateGPT API

Your Enhanced PrivateGPT is now ready for production use! 🚀
