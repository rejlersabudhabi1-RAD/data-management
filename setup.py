#!/usr/bin/env python
"""
Quick setup script for Data Management Service
Run this after initial installation to set up the service
"""

import os
import sys
import subprocess
import secrets


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def run_command(command, description):
    """Run a shell command and report status"""
    print(f"→ {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"  ✓ Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed: {e}")
        print(f"  Error output: {e.stderr}")
        return False


def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(50)


def create_env_file():
    """Create .env file from .env.example"""
    if os.path.exists('.env'):
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Using existing .env file")
            return
    
    print_header("Creating Environment File")
    
    # Read example file
    with open('.env.example', 'r') as f:
        content = f.read()
    
    # Generate secret key
    secret_key = generate_secret_key()
    content = content.replace('your-secret-key-here-change-in-production', secret_key)
    
    # Get user input for critical values
    print("\nPlease provide the following information:")
    
    db_password = input("PostgreSQL password (leave empty for default): ").strip()
    if db_password:
        content = content.replace('your-database-password', db_password)
    
    use_s3 = input("Use AWS S3 for file storage? (y/N): ").strip().lower() == 'y'
    if use_s3:
        content = content.replace('USE_S3=True', 'USE_S3=True')
        aws_key = input("AWS Access Key ID: ").strip()
        aws_secret = input("AWS Secret Access Key: ").strip()
        bucket_name = input("S3 Bucket Name: ").strip()
        
        content = content.replace('your-aws-access-key-id', aws_key)
        content = content.replace('your-aws-secret-access-key', aws_secret)
        content = content.replace('your-bucket-name', bucket_name)
    else:
        content = content.replace('USE_S3=True', 'USE_S3=False')
    
    jwt_secret = input("JWT Secret Key (shared with User-Management): ").strip()
    if jwt_secret:
        content = content.replace('your-jwt-secret-key-shared-with-user-management-service', jwt_secret)
    
    # Write .env file
    with open('.env', 'w') as f:
        f.write(content)
    
    print("\n✓ .env file created successfully")


def setup():
    """Main setup function"""
    print_header("Data Management Service - Setup")
    
    print("This script will help you set up the Data Management Service")
    print("Make sure you have Python 3.10+ and PostgreSQL installed\n")
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("✗ Error: manage.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Step 1: Create virtual environment
    print_header("Step 1: Virtual Environment")
    if not os.path.exists('venv'):
        if run_command('python -m venv venv', 'Creating virtual environment'):
            print("\n  Note: Activate the virtual environment:")
            if os.name == 'nt':
                print("    venv\\Scripts\\activate")
            else:
                print("    source venv/bin/activate")
    else:
        print("Virtual environment already exists")
    
    # Step 2: Install dependencies
    print_header("Step 2: Install Dependencies")
    pip_cmd = 'venv/bin/pip' if os.name != 'nt' else 'venv\\Scripts\\pip'
    run_command(f'{pip_cmd} install -r requirements.txt', 'Installing Python packages')
    
    # Step 3: Create .env file
    print_header("Step 3: Environment Configuration")
    create_env_file()
    
    # Step 4: Database setup
    print_header("Step 4: Database Setup")
    python_cmd = 'venv/bin/python' if os.name != 'nt' else 'venv\\Scripts\\python'
    
    print("\nMake sure PostgreSQL is running and the database exists.")
    print("You can create it with:")
    print("  psql -U postgres -c 'CREATE DATABASE data_management;'")
    input("\nPress Enter when ready to run migrations...")
    
    run_command(f'{python_cmd} manage.py makemigrations', 'Creating migrations')
    run_command(f'{python_cmd} manage.py migrate', 'Running migrations')
    
    # Step 5: Create superuser
    print_header("Step 5: Create Admin User")
    create_admin = input("Create superuser for admin panel? (Y/n): ").strip().lower()
    if create_admin != 'n':
        subprocess.run(f'{python_cmd} manage.py createsuperuser', shell=True)
    
    # Step 6: Collect static files
    print_header("Step 6: Collect Static Files")
    run_command(f'{python_cmd} manage.py collectstatic --noinput', 'Collecting static files')
    
    # Done!
    print_header("Setup Complete!")
    print("\n✓ Data Management Service is ready to run!\n")
    print("Next steps:")
    print("  1. Review your .env configuration")
    print("  2. Start the development server:")
    print(f"     {python_cmd} manage.py runserver")
    print("  3. Access the API at: http://localhost:8000")
    print("  4. Access admin panel at: http://localhost:8000/admin")
    print("  5. Check health endpoint: http://localhost:8000/health/")
    print("\nFor production deployment, see DEPLOYMENT.md")
    print("\n")


if __name__ == '__main__':
    try:
        setup()
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Setup failed: {e}")
        sys.exit(1)
