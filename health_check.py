"""
System Health Check Script

This script checks if all components of the Ndola Land Registry System
are working properly.

Usage: python health_check.py
"""
import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def check_mark(status):
    """Return checkmark or X based on status."""
    return f"{GREEN}✓{RESET}" if status else f"{RED}✗{RESET}"


def check_python_version():
    """Check if Python version is 3.8+."""
    print(f"\n{BLUE}Checking Python version...{RESET}")
    version = sys.version_info
    status = version.major == 3 and version.minor >= 8
    print(f"  {check_mark(status)} Python {version.major}.{version.minor}.{version.micro}")
    if not status:
        print(f"  {YELLOW}⚠  Python 3.8+ recommended{RESET}")
    return status


def check_dependencies():
    """Check if required packages are installed."""
    print(f"\n{BLUE}Checking dependencies...{RESET}")
    
    required_packages = [
        'flask',
        'sqlalchemy',
        'psycopg2',
        'geoalchemy2',
        'werkzeug',
        'flask_login',
        'pytesseract',
        'PIL',
        'reportlab',
        'shapely',
        'sklearn'
    ]
    
    missing = []
    for package in required_packages:
        try:
            if package == 'PIL':
                __import__('PIL')
            elif package == 'sklearn':
                __import__('sklearn')
            else:
                __import__(package)
            print(f"  {check_mark(True)} {package}")
        except ImportError:
            print(f"  {check_mark(False)} {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n  {YELLOW}Missing packages: {', '.join(missing)}{RESET}")
        print(f"  Run: pip install {' '.join(missing)}")
    
    return len(missing) == 0


def check_env_file():
    """Check if .env file exists and has required variables."""
    print(f"\n{BLUE}Checking .env configuration...{RESET}")
    
    env_path = Path('.env')
    if not env_path.exists():
        print(f"  {check_mark(False)} .env file not found")
        return False
    
    print(f"  {check_mark(True)} .env file exists")
    
    # Check for AWS variables (should NOT exist)
    with open('.env', 'r') as f:
        content = f.read()
        
        has_aws = any(var in content for var in ['S3_BUCKET_NAME', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'])
        if has_aws:
            print(f"  {YELLOW}⚠  Warning: AWS variables found in .env (should be removed){RESET}")
        else:
            print(f"  {check_mark(True)} No AWS variables (correct)")
        
        # Check required variables
        required = ['SECRET_KEY', 'DATABASE_URL']
        for var in required:
            has_var = var in content and not content.split(var)[1].split('\n')[0].strip() in ['', '=']
            print(f"  {check_mark(has_var)} {var}")
            if not has_var:
                return False
    
    return True


def check_database_connection():
    """Check if database connection works."""
    print(f"\n{BLUE}Checking database connection...{RESET}")
    
    try:
        from app import app, db
        with app.app_context():
            # Try a simple query
            db.session.execute('SELECT 1')
            print(f"  {check_mark(True)} Database connection successful")
            
            # Check tables exist
            tables = db.session.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """).fetchall()
            
            required_tables = [
                'users', 'land_applications', 'documents', 
                'land_parcels', 'land_conflicts'
            ]
            
            existing = [t[0] for t in tables]
            for table in required_tables:
                has_table = table in existing
                print(f"  {check_mark(has_table)} Table: {table}")
            
            return all(table in existing for table in required_tables)
            
    except Exception as e:
        print(f"  {check_mark(False)} Database connection failed: {e}")
        return False


def check_uploads_directory():
    """Check if uploads directory exists and is writable."""
    print(f"\n{BLUE}Checking uploads directory...{RESET}")
    
    upload_dir = Path('uploads')
    
    # Check existence
    if not upload_dir.exists():
        print(f"  {check_mark(False)} uploads/ directory not found")
        try:
            upload_dir.mkdir()
            print(f"  {check_mark(True)} Created uploads/ directory")
        except Exception as e:
            print(f"  {check_mark(False)} Could not create directory: {e}")
            return False
    else:
        print(f"  {check_mark(True)} uploads/ directory exists")
    
    # Check writability
    test_file = upload_dir / '.write_test'
    try:
        test_file.write_text('test')
        test_file.unlink()
        print(f"  {check_mark(True)} Directory is writable")
        return True
    except Exception as e:
        print(f"  {check_mark(False)} Directory not writable: {e}")
        return False


def check_ai_modules():
    """Check if AI modules are present and can be imported."""
    print(f"\n{BLUE}Checking AI modules...{RESET}")
    
    modules = [
        'ai_conflict',
        'ai_conflict_enhanced',
        'duplicate_detector',
        'document_processing',
        'validation_utils'
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print(f"  {check_mark(True)} {module}.py")
        except Exception as e:
            print(f"  {check_mark(False)} {module}.py - {str(e)[:50]}")
            all_ok = False
    
    return all_ok


def check_tesseract():
    """Check if Tesseract OCR is installed."""
    print(f"\n{BLUE}Checking Tesseract OCR...{RESET}")
    
    try:
        import pytesseract
        from PIL import Image
        
        # Try to get Tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"  {check_mark(True)} Tesseract {version} installed")
        return True
    except Exception as e:
        print(f"  {check_mark(False)} Tesseract not found or not configured")
        print(f"  {YELLOW}⚠  Install from: https://github.com/UB-Mannheim/tesseract/wiki{RESET}")
        return False


def check_aws_removal():
    """Check if AWS code has been removed from app.py."""
    print(f"\n{BLUE}Checking AWS code removal...{RESET}")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for AWS imports
        has_boto3 = 'import boto3' in content
        has_botocore = 'from botocore' in content
        has_s3 = 'S3_BUCKET_NAME' in content
        
        if not any([has_boto3, has_botocore, has_s3]):
            print(f"  {check_mark(True)} No AWS code found (correct)")
            return True
        else:
            print(f"  {check_mark(False)} AWS code still present:")
            if has_boto3:
                print(f"      - boto3 import found")
            if has_botocore:
                print(f"      - botocore import found")
            if has_s3:
                print(f"      - S3 references found")
            print(f"  {YELLOW}⚠  See QUICK_FIX_GUIDE.md for removal instructions{RESET}")
            return False
            
    except Exception as e:
        print(f"  {check_mark(False)} Could not check app.py: {e}")
        return False


def check_model_relationships():
    """Check if model relationships are properly configured."""
    print(f"\n{BLUE}Checking model relationships...{RESET}")
    
    try:
        from models import LandApplication, LandParcel, LandConflict
        from app import app, db
        
        with app.app_context():
            # Check if relationships work
            app_count = LandApplication.query.count()
            print(f"  {check_mark(True)} LandApplication model OK ({app_count} records)")
            
            parcel_count = LandParcel.query.count()
            print(f"  {check_mark(True)} LandParcel model OK ({parcel_count} records)")
            
            conflict_count = LandConflict.query.count()
            print(f"  {check_mark(True)} LandConflict model OK ({conflict_count} records)")
            
            return True
            
    except Exception as e:
        print(f"  {check_mark(False)} Model relationship error: {e}")
        return False


def run_all_checks():
    """Run all health checks."""
    print(f"\n{'='*70}")
    print(f"{BLUE}NDOLA LAND REGISTRY SYSTEM - HEALTH CHECK{RESET}")
    print(f"{'='*70}")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment Config", check_env_file),
        ("Database Connection", check_database_connection),
        ("Uploads Directory", check_uploads_directory),
        ("AI Modules", check_ai_modules),
        ("Tesseract OCR", check_tesseract),
        ("AWS Removal", check_aws_removal),
        ("Model Relationships", check_model_relationships),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n{RED}Error running {name} check: {e}{RESET}")
            results.append((name, False))
    
    # Summary
    print(f"\n{'='*70}")
    print(f"{BLUE}SUMMARY{RESET}")
    print(f"{'='*70}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        print(f"  {check_mark(result)} {name}")
    
    print(f"\n  {passed}/{total} checks passed")
    
    if passed == total:
        print(f"\n  {GREEN}✓ System is healthy and ready to use!{RESET}")
    elif passed >= total * 0.7:
        print(f"\n  {YELLOW}⚠ System is mostly healthy but has some issues{RESET}")
    else:
        print(f"\n  {RED}✗ System has critical issues that need attention{RESET}")
    
    print(f"\n{'='*70}\n")
    
    return passed == total


if __name__ == '__main__':
    try:
        success = run_all_checks()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Health check interrupted{RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Fatal error: {e}{RESET}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
