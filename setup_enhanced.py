"""Setup script for Enhanced PrivateGPT - creates database and default users."""
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from private_gpt.auth.models import User, UserRole, UserCreate
from private_gpt.auth.auth_service import AuthService
from private_gpt.di import create_injector
from private_gpt.components.llm.llm_component import LLMComponent
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

async def setup_database():
    """Initialize database and create default users."""
    print("🔧 Setting up Enhanced PrivateGPT Database...")
    
    try:
        # Create injector to get dependencies
        injector = create_injector()
        auth_service = injector.get(AuthService)
        
        print("✅ Dependency injection setup complete")
        
        # Create database tables
        from private_gpt.auth.models import Base
        
        # Get database engine from auth service
        engine = auth_service.engine
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created")
        
        # Create default users
        default_users = [
            {
                "username": "superadmin",
                "email": "superadmin@example.com",
                "password": "admin123!",
                "role": UserRole.SUPERADMIN
            },
            {
                "username": "admin", 
                "email": "admin@example.com",
                "password": "admin123!",
                "role": UserRole.ADMIN
            },
            {
                "username": "user",
                "email": "user@example.com", 
                "password": "user123!",
                "role": UserRole.USER
            }
        ]
        
        for user_data in default_users:
            try:
                # Check if user already exists
                existing_user = auth_service.get_user_by_username(user_data["username"])
                if existing_user:
                    print(f"⚠️  User {user_data['username']} already exists, skipping...")
                    continue
                
                # Create new user
                user_create = UserCreate(
                    username=user_data["username"],
                    email=user_data["email"],
                    password=user_data["password"],
                    role=user_data["role"]
                )
                
                new_user = auth_service.create_user(user_create)
                print(f"✅ Created {user_data['role'].value} user: {user_data['username']}")
                
            except Exception as e:
                print(f"❌ Failed to create user {user_data['username']}: {e}")
        
        print("\n🎉 Database setup complete!")
        print("\nDefault users created:")
        print("   • superadmin:admin123! (SuperAdmin)")
        print("   • admin:admin123! (Admin)")
        print("   • user:user123! (User)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_simple_database():
    """Create a simple SQLite database if no database is configured."""
    try:
        # Check if database file exists
        db_path = Path("./private_gpt_enhanced.db")
        
        if not db_path.exists():
            print(f"📁 Creating SQLite database at: {db_path}")
            
            # Create simple SQLite engine
            from sqlalchemy import create_engine
            engine = create_engine(f"sqlite:///{db_path}")
            
            # Create tables
            from private_gpt.auth.models import Base
            Base.metadata.create_all(bind=engine)
            
            print("✅ SQLite database created")
            return True
        else:
            print(f"📁 Database already exists at: {db_path}")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

async def main():
    """Main setup function."""
    print("🚀 Enhanced PrivateGPT Setup")
    print("="*50)
    
    # Try to create simple database first
    if not create_simple_database():
        print("❌ Failed to create database")
        return False
    
    # Setup database and users
    success = await setup_database()
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the server: python enhanced_main.py")
        print("2. Run tests: python test_enhanced.py")
        print("3. Open web interface: http://localhost:8001/docs")
    else:
        print("\n❌ Setup failed!")
        
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
