"""
Inspect DB helper

Run with the project's virtualenv python to print counts and sample test rows.
Usage:
  .\.venv\Scripts\python.exe scripts\inspect_db.py

This script loads the Flask app context and queries the models for quick checks.
"""

import os
import sys

# Ensure project root is first on sys.path so local modules are preferred over installed packages
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app
from models import db, LandParcel, LandApplication

with app.app_context():
    try:
        # Print the SQLALCHEMY_DATABASE_URI being used so we can confirm which DB is targeted
        print("Using SQLALCHEMY_DATABASE_URI:", app.config.get('SQLALCHEMY_DATABASE_URI'))
        # List tables in the connected database
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("Tables in DB:", tables)
        parcel_count = LandParcel.query.count()
        app_count = LandApplication.query.count()
        print(f"LandParcel count: {parcel_count}")
        print(f"LandApplication count: {app_count}")

        test_parcels = LandParcel.query.filter(LandParcel.parcel_number.like('TEST-%')).all()
        print(f"Test parcels found: {len(test_parcels)}")
        for p in test_parcels:
            coords = 'yes' if getattr(p, 'coordinates', None) is not None else 'no'
            print(f"  {p.parcel_number} | owner_nrc={p.owner_nrc} | location={p.location} | coords={coords}")

        test_apps = LandApplication.query.filter(LandApplication.reference_number.like('TEST-APP-%')).all()
        print(f"Test applications found: {len(test_apps)}")
        for a in test_apps:
            coords = 'yes' if getattr(a, 'coordinates', None) is not None else 'no'
            print(f"  {a.reference_number} | nrc={a.nrc_number} | location={a.land_location} | coords={coords}")

    except Exception as e:
        print('Error inspecting DB:', e)
        raise
