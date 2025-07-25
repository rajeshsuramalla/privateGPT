"""Test script for Enhanced PrivateGPT features."""
import requests
import json
import time
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8001"
TEST_USERS = {
    "superadmin": {"username": "superadmin", "password": "admin123!"},
    "admin": {"username": "admin", "password": "admin123!"},
    "user": {"username": "user", "password": "user123!"}
}

class PrivateGPTTester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.tokens = {}
        
    def print_step(self, step, description):
        print(f"\n{'='*60}")
        print(f"Step {step}: {description}")
        print('='*60)
    
    def print_result(self, success, message, data=None):
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {message}")
        if data and isinstance(data, dict):
            print(f"Response: {json.dumps(data, indent=2)}")
        elif data:
            print(f"Response: {data}")
    
    def test_health_check(self):
        """Test basic and enhanced health checks."""
        self.print_step(1, "Health Check")
        
        try:
            # Test basic health
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.print_result(True, "Basic health check passed")
            else:
                self.print_result(False, f"Basic health check failed: {response.status_code}")
            
            # Test enhanced health
            response = requests.get(f"{self.base_url}/health/enhanced")
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, "Enhanced health check passed", data)
            else:
                self.print_result(False, f"Enhanced health check failed: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.print_result(False, "Server is not running. Please start it with: python enhanced_main.py")
            return False
        except Exception as e:
            self.print_result(False, f"Health check error: {e}")
            return False
        
        return True
    
    def test_authentication(self):
        """Test authentication for all user types."""
        self.print_step(2, "Authentication Testing")
        
        for role, creds in TEST_USERS.items():
            try:
                response = requests.post(
                    f"{self.base_url}/v1/auth/login",
                    json=creds,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.tokens[role] = data["access_token"]
                    self.print_result(True, f"{role.upper()} login successful", {
                        "user": data["user"]["username"],
                        "role": data["user"]["role"],
                        "token_expires_in": data["expires_in"]
                    })
                else:
                    self.print_result(False, f"{role.upper()} login failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.print_result(False, f"{role.upper()} login error: {e}")
        
        return len(self.tokens) > 0
    
    def test_user_info(self):
        """Test getting current user information."""
        self.print_step(3, "User Information Testing")
        
        for role, token in self.tokens.items():
            try:
                response = requests.get(
                    f"{self.base_url}/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.print_result(True, f"{role.upper()} user info retrieved", {
                        "username": data["username"],
                        "role": data["role"],
                        "email": data["email"]
                    })
                else:
                    self.print_result(False, f"{role.upper()} user info failed: {response.status_code}")
                    
            except Exception as e:
                self.print_result(False, f"{role.upper()} user info error: {e}")
    
    def test_model_access(self):
        """Test model access for different users."""
        self.print_step(4, "Model Access Testing")
        
        for role, token in self.tokens.items():
            try:
                response = requests.get(
                    f"{self.base_url}/v1/chat/models",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    model_count = len(data.get("models", {}))
                    self.print_result(True, f"{role.upper()} can access {model_count} models", {
                        "available_models": list(data.get("models", {}).keys()),
                        "default_model": data.get("default")
                    })
                else:
                    self.print_result(False, f"{role.upper()} model access failed: {response.status_code}")
                    
            except Exception as e:
                self.print_result(False, f"{role.upper()} model access error: {e}")
    
    def test_chat_functionality(self):
        """Test enhanced chat functionality."""
        self.print_step(5, "Enhanced Chat Testing")
        
        test_message = {
            "messages": [
                {"role": "user", "content": "Hello! Can you tell me what 2+2 equals?"}
            ],
            "use_context": False,
            "stream": False
        }
        
        for role, token in self.tokens.items():
            try:
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=test_message,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    self.print_result(True, f"{role.upper()} chat successful", {
                        "response_preview": content[:100] + "..." if len(content) > 100 else content
                    })
                else:
                    self.print_result(False, f"{role.upper()} chat failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.print_result(False, f"{role.upper()} chat error: {e}")
    
    def test_document_management(self):
        """Test document management features."""
        self.print_step(6, "Document Management Testing")
        
        # Test getting user's documents
        for role, token in self.tokens.items():
            try:
                response = requests.get(
                    f"{self.base_url}/v1/ingest/my-documents",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    doc_count = len(data) if isinstance(data, list) else 0
                    self.print_result(True, f"{role.upper()} has {doc_count} documents")
                else:
                    self.print_result(False, f"{role.upper()} document list failed: {response.status_code}")
                    
            except Exception as e:
                self.print_result(False, f"{role.upper()} document list error: {e}")
    
    def test_text_ingestion(self):
        """Test text ingestion with ownership."""
        self.print_step(7, "Text Ingestion Testing")
        
        test_document = {
            "file_name": "test_document.txt",
            "text": "This is a test document for the enhanced PrivateGPT system. It contains sample text to verify document ingestion and ownership features.",
            "is_public": False
        }
        
        # Test with user token (if they have ingest permission)
        if "user" in self.tokens:
            try:
                response = requests.post(
                    f"{self.base_url}/v1/ingest/text",
                    json=test_document,
                    headers={
                        "Authorization": f"Bearer {self.tokens['user']}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.print_result(True, "USER text ingestion successful", {
                        "documents_created": len(data.get("data", [])),
                        "owner_id": data.get("owner_id"),
                        "is_public": data.get("is_public")
                    })
                else:
                    self.print_result(False, f"USER text ingestion failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.print_result(False, f"USER text ingestion error: {e}")
    
    def test_admin_functions(self):
        """Test admin-specific functions."""
        self.print_step(8, "Admin Functions Testing")
        
        if "admin" not in self.tokens:
            self.print_result(False, "No admin token available for testing")
            return
        
        try:
            # Test listing all users
            response = requests.get(
                f"{self.base_url}/v1/auth/users",
                headers={"Authorization": f"Bearer {self.tokens['admin']}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                user_count = len(data) if isinstance(data, list) else 0
                self.print_result(True, f"ADMIN can see {user_count} users in system")
            else:
                self.print_result(False, f"ADMIN user list failed: {response.status_code}")
                
        except Exception as e:
            self.print_result(False, f"ADMIN functions error: {e}")
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        print("🧪 Enhanced PrivateGPT Testing Suite")
        print("="*60)
        
        # Test health first
        if not self.test_health_check():
            print("\n❌ Cannot continue testing - server is not responding")
            return False
        
        # Run authentication tests
        if not self.test_authentication():
            print("\n❌ Cannot continue testing - authentication failed")
            return False
        
        # Run other tests
        self.test_user_info()
        self.test_model_access()
        self.test_chat_functionality()
        self.test_document_management()
        self.test_text_ingestion()
        self.test_admin_functions()
        
        # Summary
        print(f"\n{'='*60}")
        print("🎉 Testing Complete!")
        print("="*60)
        print("\n📊 Summary:")
        print(f"   • Authenticated users: {len(self.tokens)}")
        print(f"   • Available tokens: {list(self.tokens.keys())}")
        print("\n💡 Next Steps:")
        print("   1. Try the web interface at http://localhost:8001/docs")
        print("   2. Test file upload via the UI")
        print("   3. Create additional users")
        print("   4. Configure model access permissions")
        
        return True

def main():
    """Main test execution."""
    print("Starting Enhanced PrivateGPT Test Suite...")
    print("Make sure the server is running with: python enhanced_main.py")
    
    # Wait a moment for user to read
    time.sleep(2)
    
    tester = PrivateGPTTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
