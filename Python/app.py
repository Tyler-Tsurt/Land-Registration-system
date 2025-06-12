import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from datetime import timedelta, datetime
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename # For secure file naming

app = Flask(__name__)

# --- JWT Configuration ---
app.config["JWT_SECRET_KEY"] = "super-secret-jwt-key-change-this-in-production"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)

# --- Database Configuration (PostgreSQL) ---
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://ndola_user:Trust%402517@localhost:5432/ndola_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- File Upload Configuration ---
# Define the base upload folder relative to the app.py location
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure the UPLOAD_FOLDER exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"Created UPLOAD_FOLDER: {UPLOAD_FOLDER}")


# --- Define Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_names = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)

    # Relationship to LandApplication (one user can have many applications)
    applications = db.relationship('LandApplication', backref='applicant', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class LandApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    land_location = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending', nullable=False) # e.g., Pending, Under Review, Approved, Rejected
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    # Store paths to directories or specific files
    pictures_folder_path = db.Column(db.String(255), nullable=True)
    documents_folder_path = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<LandApplication {self.id} - {self.land_location}>'


# --- CORS Configuration ---
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# --- Role-Based Access Control Decorator ---
def role_required(required_role):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            current_user_email = get_jwt_identity()
            user = User.query.filter_by(email=current_user_email).first()
            if user and user.role == required_role:
                return fn(*args, **kwargs)
            else:
                return jsonify({"msg": "Access forbidden: Insufficient role"}), 403
        return decorator
    return wrapper

# --- API Endpoints ---

@app.route("/api/register", methods=["POST"])
def register_user():
    data = request.get_json()
    print(f"Received registration data: {data}")

    full_names = data.get("fullNames")
    email = data.get("email")
    phone_number = data.get("phoneNumber")
    location = data.get("location")
    dob_str = data.get("dateOfBirth")
    password = data.get("password")
    confirm_password = data.get("confirmPassword")

    if not all([full_names, email, phone_number, location, dob_str, password, confirm_password]):
        print("Registration failed: Missing fields")
        return jsonify({"msg": "All fields are required"}), 400
    if password != confirm_password:
        print("Registration failed: Passwords do not match")
        return jsonify({"msg": "Passwords do not match"}), 400
    if len(password) < 8:
        print("Registration failed: Password too short")
        return jsonify({"msg": "Password must be at least 8 characters"}), 400

    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
    except ValueError:
        print(f"Registration failed: Invalid DOB format '{dob_str}'")
        return jsonify({"msg": "Invalid date format for Date of Birth"}), 400

    if User.query.filter_by(email=email).first():
        print(f"Registration failed: Email '{email}' already registered")
        return jsonify({"msg": "Email already registered"}), 409

    hashed_password = generate_password_hash(password)
    
    new_user = User(
        full_names=full_names,
        email=email,
        phone_number=phone_number,
        location=location,
        date_of_birth=dob,
        password_hash=hashed_password,
        role="user"
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        print(f"User '{email}' registered successfully and committed to DB.")
        
        # Automatic login after successful registration
        access_token = create_access_token(identity=new_user.email, additional_claims={"role": new_user.role})
        return jsonify(msg="Registration successful!", access_token=access_token, role=new_user.role), 201
    except Exception as e:
        db.session.rollback()
        print(f"Database error during registration: {e}")
        return jsonify({"msg": "Database error during registration"}), 500

@app.route("/api/login", methods=["POST"])
def login_user():
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    print(f"Login attempt for email: {email}")
    user = User.query.filter_by(email=email).first()

    if user:
        print(f"User found: {user.email}")
        password_matches = check_password_hash(user.password_hash, password)
        print(f"Password check result for {email}: {password_matches}")
    else:
        print(f"User '{email}' not found in database.")
        password_matches = False

    if not user or not password_matches:
        print(f"Login failed for {email}: Bad email or password.")
        return jsonify({"msg": "Bad email or password"}), 401

    access_token = create_access_token(identity=user.email, additional_claims={"role": user.role})
    print(f"User '{user.email}' logged in successfully with role: {user.role}")
    return jsonify(access_token=access_token, role=user.role)

@app.route("/api/user/dashboard", methods=["GET"])
@jwt_required()
def user_dashboard():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    if user and user.role == 'user':
        return jsonify({
            "msg": f"Welcome to your User Dashboard, {user.full_names}!",
            "user_info": {
                "email": user.email,
                "location": user.location,
                "phone_number": user.phone_number
            },
            "data": "Here is some personalized user data."
        }), 200
    else:
        print(f"Access forbidden for user '{current_user_email}': Role is not 'user' or user not found.")
        return jsonify({"msg": "Access forbidden: Not a user or invalid token"}), 403

@app.route("/api/admin/dashboard", methods=["GET"])
@role_required("admin")
def admin_dashboard():
    current_admin_email = get_jwt_identity()
    all_users = User.query.all()
    users_list_preview = [user.email for user in all_users[:5]]

    return jsonify({
        "msg": f"Welcome to the Admin Dashboard, {current_admin_email}!",
        "all_users_count": len(all_users),
        "users_list_preview": users_list_preview,
        "admin_specific_data": "Critical system insights and controls."
    }), 200

@app.route("/api/apply_land", methods=["POST"])
@jwt_required()
def apply_land():
    current_user_email = get_jwt_identity()
    applicant = User.query.filter_by(email=current_user_email).first()

    if not applicant:
        return jsonify({"msg": "Applicant not found."}), 404

    # Get form data
    land_location = request.form.get('landLocation')
    
    if not land_location:
        return jsonify({"msg": "Land location is required."}), 400

    # Create a new LandApplication entry
    new_application = LandApplication(
        applicant_id=applicant.id,
        land_location=land_location,
        status='Pending'
    )
    db.session.add(new_application)
    db.session.commit() # Commit to get an ID for folder naming

    application_id = new_application.id
    
    # Create structured folders for uploads
    user_upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(applicant.id))
    application_folder = os.path.join(user_upload_folder, f"app_{application_id}")
    pictures_folder = os.path.join(application_folder, 'pictures')
    documents_folder = os.path.join(application_folder, 'documents')

    os.makedirs(pictures_folder, exist_ok=True)
    os.makedirs(documents_folder, exist_ok=True)

    # Save pictures
    pictures_saved_paths = []
    if 'pictures' in request.files:
        for file in request.files.getlist('pictures'):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(pictures_folder, filename)
                file.save(filepath)
                pictures_saved_paths.append(filepath)
                print(f"Saved picture: {filepath}")
            else:
                print(f"Skipped invalid picture file: {file.filename}")

    # Save documents
    documents_saved_paths = []
    if 'documents' in request.files:
        for file in request.files.getlist('documents'):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(documents_folder, filename)
                file.save(filepath)
                documents_saved_paths.append(filepath)
                print(f"Saved document: {filepath}")
            else:
                print(f"Skipped invalid document file: {file.filename}")

    # Update LandApplication record with folder paths
    new_application.pictures_folder_path = pictures_folder
    new_application.documents_folder_path = documents_folder
    db.session.commit() # Commit updated paths

    return jsonify({
        "msg": "Land application submitted successfully!",
        "application_id": application_id,
        "pictures_uploaded": pictures_saved_paths,
        "documents_uploaded": documents_saved_paths
    }), 200


# --- Run the App and Create Tables ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all() # Creates tables based on your models if they don't exist

        admin_email = 'admin@example.com'
        if not User.query.filter_by(email=admin_email).first():
            admin_user = User(
                full_names='Default Admin',
                email=admin_email,
                phone_number='0971000000',
                location='Admin HQ',
                date_of_birth=datetime(1980, 1, 1).date(),
                password_hash=generate_password_hash('adminpass'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created.")
        else:
            print("Default admin user already exists.")

    app.run(debug=True, port=5000)
