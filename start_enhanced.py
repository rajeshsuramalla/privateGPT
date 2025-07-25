"""Simple startup script for Enhanced PrivateGPT."""
import subprocess
import sys
import time
import requests

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['bcrypt', 'PyJWT', 'python-multipart', 'SQLAlchemy', 'alembic']
    from typing import List
    missing: List[str] = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("Installing missing dependencies...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing, check=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False
    else:
        print("✅ All dependencies are installed")
    
    return True

def start_server():
    """Start the enhanced PrivateGPT server."""
    print("🚀 Starting Enhanced PrivateGPT server...")
    
    try:
        # Start the server
        process = subprocess.Popen([
            sys.executable, 'enhanced_main.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is responding
        for _ in range(10):
            try:
                response = requests.get('http://localhost:8001/health', timeout=2)
                if response.status_code == 200:
                    print("✅ Server is running at http://localhost:8001")
                    print("📖 API Documentation: http://localhost:8001/docs")
                    return process
            except requests.exceptions.RequestException:
                time.sleep(1)
                continue
        
        print("❌ Server failed to start properly")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def create_test_users():
    """Create default test users."""
    print("👥 Creating test users...")
    
    users = [
        {"username": "superadmin", "email": "superadmin@example.com", "password": "admin123!", "role": "SUPERADMIN"},
        {"username": "admin", "email": "admin@example.com", "password": "admin123!", "role": "ADMIN"}, 
        {"username": "user", "email": "user@example.com", "password": "user123!", "role": "USER"}
    ]
    
    created_count = 0
    for user_data in users:
        try:
            response = requests.post(
                'http://localhost:8001/v1/auth/register',
                json=user_data,
                timeout=5
            )
            if response.status_code == 200:
                print(f"✅ Created user: {user_data['username']} ({user_data['role']})")
                created_count += 1
            elif response.status_code == 400:
                print(f"⚠️  User {user_data['username']} already exists")
            else:
                print(f"❌ Failed to create user {user_data['username']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error creating user {user_data['username']}: {e}")
    
    if created_count > 0:
        print(f"✅ Created {created_count} new users")
    
    return True

def show_test_commands():
    """Show test commands for the user."""
    print("\n" + "="*60)
    print("🧪 TESTING COMMANDS")
    print("="*60)
    
    print("\n1. Test login (PowerShell):")
    print('curl -X POST "http://localhost:8001/v1/auth/login" `')
    print('  -H "Content-Type: application/json" `')
    print('  -d \'{"username": "superadmin", "password": "admin123!"}\'')
    
    print("\n2. Test health check:")
    print('curl http://localhost:8001/health')
    
    print("\n3. Run automated tests:")
    print('python test_enhanced.py')
    
    print("\n4. Web interface:")
    print('Open: http://localhost:8001/docs')
    
    print("\n📝 Default test credentials:")
    print("   • superadmin:admin123! (SuperAdmin)")
    print("   • admin:admin123! (Admin)")
    print("   • user:user123! (User)")

def main():
    """Main startup function."""
    print("🚀 Enhanced PrivateGPT Startup")
    print("="*50)
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Start server
    process = start_server()
    if not process:
        return False
    
    # Create test users
    create_test_users()
    
    # Show test commands
    show_test_commands()
    
    print(f"\n{'='*60}")
    print("✅ Enhanced PrivateGPT is ready!")
    print("Press Ctrl+C to stop the server")
    print("="*60)
    
    try:
        # Keep the server running
        process.wait()
    except KeyboardInterrupt:
        print("\n⚠️  Stopping server...")
        process.terminate()
        process.wait()
        print("✅ Server stopped")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
