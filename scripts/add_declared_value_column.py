"""
Run this script to add the `declared_value` column to the `land_applications` table if it doesn't exist.
Usage (from repository root, with your venv active):
    python scripts/add_declared_value_column.py

This connects using the same DATABASE_URL your Flask app uses, runs a safe `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.
"""
from dotenv import load_dotenv
load_dotenv()
import os
from flask import Flask
from models import db

# create minimal Flask app using your app configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# initialize db
db.init_app(app)

ALTER_SQL = """
ALTER TABLE land_applications
ADD COLUMN IF NOT EXISTS declared_value DOUBLE PRECISION DEFAULT 0.0;
"""

if __name__ == '__main__':
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        print('ERROR: DATABASE_URL environment variable is not set. Please set it in your .env or environment.')
        raise SystemExit(1)

    with app.app_context():
        conn = db.engine.connect()
        try:
            print('Checking and adding declared_value column if necessary...')
            conn.execute(ALTER_SQL)
            print('ALTER completed (if column did not exist it was added).')
        except Exception as e:
            print('Error running ALTER TABLE:', e)
            raise
        finally:
            conn.close()
