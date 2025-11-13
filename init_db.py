from dotenv import load_dotenv
load_dotenv()
import argparse
import sys
from flask import Flask
from models import db, User, SystemSettings, LandApplication, LandParcel, LandConflict
from werkzeug.security import generate_password_hash
from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon
from datetime import datetime
import os
import secrets

def create_app():
    """Create Flask application for database initialization"""
    app = Flask(__name__)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]

    db.init_app(app)
    return app

def init_database():
    """Initialize database with tables and default data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Drop all tables (use with caution in production!)
            print("Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            
            # Create default admin user
            print("Creating default admin user...")
            
            # Create a user object and set the password using the set_password method
            admin = User(
                username='admin',
                email='admin@ndolalands.gov.zm',
                first_name='System',
                last_name='Administrator',
                role='super_admin',
                phone_number='+260971000000'
            )
            admin.set_password('admin123')
            
            # Create ministry admin user
            ministry_admin = User(
                username='ministry_admin',
                email='ministry@lands.gov.zm',
                first_name='Ministry',
                last_name='Officer',
                role='admin',
                phone_number='+260971000001'
            )
            ministry_admin.set_password('ministry123')
            
            # Create city council admin
            council_admin = User(
                username='council_admin',
                email='council@ndola.gov.zm',
                first_name='Council',
                last_name='Officer',
                role='admin',
                phone_number='+260971000002'
            )
            council_admin.set_password('council123')
            
            # Create test citizen user
            citizen = User(
                username='citizen_test',
                email='citizen@example.com',
                first_name='Test',
                last_name='Citizen',
                role='citizen',
                phone_number='+260971234567'
            )
            citizen.set_password('citizen123')
            
            db.session.add(admin)
            db.session.add(ministry_admin)
            db.session.add(council_admin)
            db.session.add(citizen)
            
            # Create default system settings
            print("Creating system settings...")
            default_settings = [
                # AI Settings
                ('ai_conflict_threshold', '0.7', 'float', 'AI confidence threshold for conflict detection', 'ai'),
                ('ai_duplicate_threshold', '0.8', 'float', 'AI confidence threshold for duplicate detection', 'ai'),
                ('auto_approval_threshold', '0.95', 'float', 'AI confidence threshold for automatic approval', 'ai'),
                ('ai_processing_enabled', 'true', 'boolean', 'Enable AI processing for applications', 'ai'),
                
                # File Upload Settings
                ('max_file_size', '5242880', 'integer', 'Maximum file upload size in bytes (5MB)', 'upload'),
                ('allowed_file_types', 'pdf,jpg,jpeg,png', 'string', 'Allowed file types for document upload', 'upload'),
                ('upload_path', 'uploads', 'string', 'Directory for uploaded files', 'upload'),
                
                # Processing Settings
                ('processing_fee', '500.00', 'float', 'Land registration processing fee in ZMW', 'processing'),
                ('processing_time_days', '30', 'integer', 'Standard processing time in days', 'processing'),
                ('priority_processing_fee', '1000.00', 'float', 'Priority processing fee in ZMW', 'processing'),
                
                # System Settings
                ('system_name', 'Ndola Land Registry System', 'string', 'System name', 'system'),
                ('system_version', '1.0.0', 'string', 'System version', 'system'),
                ('maintenance_mode', 'false', 'boolean', 'Enable maintenance mode', 'system'),
                ('timezone', 'Africa/Lusaka', 'string', 'System timezone', 'system'),
                
                # Notification Settings
                ('email_enabled', 'true', 'boolean', 'Enable email notifications', 'notification'),
                ('sms_enabled', 'false', 'boolean', 'Enable SMS notifications', 'notification'),
                ('admin_notification_email', 'admin@ndolalands.gov.zm', 'string', 'Admin notification email', 'notification'),
                
                # Security Settings
                ('session_timeout', '3600', 'integer', 'Session timeout in seconds', 'security'),
                ('max_login_attempts', '5', 'integer', 'Maximum login attempts before lockout', 'security'),
                ('lockout_duration', '900', 'integer', 'Account lockout duration in seconds', 'security'),
                
                # GIS Settings
                ('default_srid', '4326', 'integer', 'Default spatial reference system ID', 'gis'),
                ('map_center_lat', '-12.9640', 'float', 'Default map center latitude (Ndola)', 'gis'),
                ('map_center_lng', '28.6367', 'float', 'Default map center longitude (Ndola)', 'gis'),
                ('default_zoom_level', '12', 'integer', 'Default map zoom level', 'gis'),
            ]
            
            for key, value, setting_type, desc, category in default_settings:
                setting = SystemSettings(
                    setting_key=key,
                    setting_value=value,
                    setting_type=setting_type,
                    description=desc,
                    category=category,
                    is_system=True,
                    updated_by=1  # Admin user
                )
                db.session.add(setting)
            
            # Commit all changes
            db.session.commit()
            print("Database initialized successfully!")
            
            # Display created users
            print("\n=== Created Users ===")
            users = User.query.all()
            for user in users:
                print(f"Username: {user.username}, Email: {user.email}, Role: {user.role}")
            
            print(f"\n=== System Settings Created: {len(default_settings)} ===")
            print("Database initialization completed!")
            
        except Exception as e:
            print(f"Error during database initialization: {str(e)}")
            db.session.rollback()
            raise

def create_sample_data():
    """Create sample applications and data for testing"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Creating sample applications...")
            
            # Get admin user for reviewed_by field
            admin = User.query.filter_by(username='admin').first()
            
            # Sample applications
            sample_applications = [
                {
                    'reference_number': 'LR-2025-0001',
                    'applicant_name': 'John Mwila',
                    'nrc_number': '123456/78/9',
                    'tpin_number': '1001234567',
                    'phone_number': '+260971234567',
                    'email': 'john.mwila@example.com',
                    'land_location': 'Chifubu, Plot 4521, House Number 23, Ndola',
                    'land_size': 2.5,
                    'land_use': 'residential',
                    'land_description': 'Residential plot for family home construction',
                    'status': 'pending',
                    'priority': 'high',
                    'ai_conflict_score': 0.85,
                    'ai_duplicate_score': 0.12,
                    'processing_fee': 500.0,
                    'payment_status': 'paid'
                },
                {
                    'reference_number': 'LR-2025-0002',
                    'applicant_name': 'Mary Phiri',
                    'nrc_number': '987654/32/1',
                    'tpin_number': '1009876543',
                    'phone_number': '+260977654321',
                    'email': 'mary.phiri@example.com',
                    'land_location': 'Kansenshi, Plot 1247, Near Kansenshi Market',
                    'land_size': 1.8,
                    'land_use': 'commercial',
                    'land_description': 'Commercial plot for retail business',
                    'status': 'under_review',
                    'priority': 'medium',
                    'ai_conflict_score': 0.15,
                    'ai_duplicate_score': 0.08,
                    'processing_fee': 750.0,
                    'payment_status': 'paid',
                    'reviewed_by': admin.id if admin else None
                },
                {

                    'land_size': 3.2,
                    'land_use': 'agricultural',
                    'land_description': 'Agricultural land for crop farming',
                    'status': 'approved',
                    'priority': 'low',
                    'ai_conflict_score': 0.05,
                    'ai_duplicate_score': 0.03,
                    'processing_fee': 500.0,
                    'payment_status': 'paid',
                    'reviewed_by': admin.id if admin else None
                },
                {
                    'reference_number': 'LR-2025-0004',
                    'applicant_name': 'Grace Tembo',
                    'nrc_number': '321987/65/4',
                    'tpin_number': '1003219876',
                    'phone_number': '+260976543210',
                    'email': 'grace.tembo@example.com',
                    'land_location': 'Northrise, Plot 334, Northrise Extension',
                    'land_size': 1.5,
                    'land_use': 'residential',
                    'land_description': 'Residential plot in upmarket area',
                    'status': 'pending',
                    'priority': 'high',
                    'ai_conflict_score': 0.92,
                    'ai_duplicate_score': 0.78,
                    'processing_fee': 500.0,
                    'payment_status': 'pending'
                },
                {
                    'reference_number': 'LR-2025-0005',
                    'applicant_name': 'Peter Mukuka',
                    'nrc_number': '159753/48/6',
                    'tpin_number': '1001597534',
                    'phone_number': '+260955789123',
                    'email': 'peter.mukuka@example.com',
                    'land_location': 'Chipulukusu, Plot 567, Near Chipulukusu Market',
                    'land_size': 2.0,
                    'land_use': 'mixed',
                    'land_description': 'Mixed use development - residential and small business',
                    'status': 'rejected',
                    'priority': 'medium',
                    'ai_conflict_score': 0.95,
                    'ai_duplicate_score': 0.89,
                    'processing_fee': 500.0,
                    'payment_status': 'paid',
                    'reviewed_by': admin.id if admin else None,
                    'rejection_reason': 'Overlaps with existing parcel ND-2024-00123'
                }
            ]
            
            for app_data in sample_applications:
                existing = LandApplication.query.filter_by(reference_number=app_data['reference_number']).first()
                if not existing:
                    application = LandApplication(**app_data)
                    db.session.add(application)
            
            # Sample land parcels (already registered)
            print("Creating sample land parcels...")
            sample_parcels = [
                {
                    'parcel_number': 'ND-2024-00123',
                    'certificate_number': 'CERT-2024-00123',
                    'owner_name': 'James Mulenga',
                    'owner_nrc': '112233/44/5',
                    'owner_phone': '+260971112233',
                    'owner_email': 'james.mulenga@example.com',
                    'location': 'Chipulukusu, Plot 566, Adjacent to Market Area',
                    'size': 1.8,
                    'land_use': 'commercial',
                    'ward': 'Chipulukusu Ward',
                    'constituency': 'Ndola Central',
                    'status': 'active',
                    'title_deed_issued': True,
                    'survey_completed': True,
                    'valuation': 250000.0,
                    'annual_tax': 2500.0
                },
                {
                    'parcel_number': 'ND-2024-00124',
                    'certificate_number': 'CERT-2024-00124',
                    'owner_name': 'Sarah Mutale',
                    'owner_nrc': '556677/88/9',
                    'owner_phone': '+260975567788',
                    'owner_email': 'sarah.mutale@example.com',
                    'location': 'Masala, Plot 790, Masala Extension',
                    'size': 2.1,
                    'land_use': 'residential',
                    'ward': 'Masala Ward',
                    'constituency': 'Ndola Central',
                    'status': 'active',
                    'title_deed_issued': True,
                    'survey_completed': True,
                    'valuation': 180000.0,
                    'annual_tax': 1800.0
                }
            ]
            
            for parcel_data in sample_parcels:
                existing = LandParcel.query.filter_by(parcel_number=parcel_data['parcel_number']).first()
                if not existing:
                    parcel = LandParcel(**parcel_data)
                    db.session.add(parcel)
            
            # Sample conflicts
            print("Creating sample conflicts...")
            
            # Get applications for conflicts
            conflict_app = LandApplication.query.filter_by(reference_number='LR-2025-0004').first()
            conflict_parcel = LandParcel.query.filter_by(parcel_number='ND-2024-00123').first()
            
            if conflict_app and conflict_parcel:
                sample_conflicts = [
                    {
                        # Removed 'conflict_id' as it does not exist in the LandConflict model
                        'conflict_type': 'overlap',
                        'title': 'Land Boundary Overlap - Northrise Area',
                        'description': 'Application LR-2025-0004 overlaps with existing parcel ND-2024-00123 by approximately 0.3 hectares',
                        'severity': 'high',
                        'status': 'unresolved',
                        'application_id': conflict_app.id,
                        'conflicting_parcel_id': conflict_parcel.id,
                        'overlap_percentage': 20.0,
                        'detected_by_ai': True,
                        'confidence_score': 0.92
                    }
                ]
                
                for conflict_data in sample_conflicts:
                    # FIX: The check for an existing conflict with a unique ID is not possible
                    # given the current model structure. Instead, we can simply add the new conflict.
                    conflict = LandConflict(**conflict_data)
                    db.session.add(conflict)
            
            db.session.commit()
            print("Sample data created successfully!")
            
            # Display summary
            applications_count = LandApplication.query.count()
            parcels_count = LandParcel.query.count()
            conflicts_count = LandConflict.query.count()
            
            print(f"\n=== Sample Data Summary ===")
            print(f"Applications created: {applications_count}")
            print(f"Land parcels created: {parcels_count}")
            print(f"Conflicts created: {conflicts_count}")
            
        except Exception as e:
            print(f"Error creating sample data: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Initialize the database and optionally create sample data')
    parser.add_argument('--yes', '-y', action='store_true', help='Run non-interactively and proceed with initialization')
    parser.add_argument('--with-sample', '-s', action='store_true', help='Also create sample data after initialization')
    args = parser.parse_args()

    print("=== Ndola Land Registry System - Database Initialization ===")
    print("This will initialize the database with tables and default data.")

    proceed = False
    if args.yes:
        proceed = True
    else:
        choice = input("Do you want to proceed? (y/n): ").lower().strip()
        proceed = choice in ['y', 'yes']

    if not proceed:
        print("Database initialization cancelled.")
        sys.exit(0)

    # Run init
    init_database()

    # Create sample data if requested
    if args.with_sample or args.yes:
        # If --with-sample was specified explicitly, or if running non-interactively
        try:
            create_sample_data()
        except Exception:
            print('Warning: creating sample data failed. Check logs for details.')

    print("\n=== Database setup completed! ===")
    print("You can now run the Flask application with: python app.py")
    print("\nDefault login credentials:")
    print("- Super Admin: admin / admin123")
    print("- Ministry Admin: ministry_admin / ministry123")
    print("- Council Admin: council_admin / council123")
    print("- Test Citizen: citizen_test / citizen123")
    print("\n*** REMEMBER TO CHANGE DEFAULT PASSWORDS IN PRODUCTION! ***")
