"""Import AI training JSON into the application's DB.

Usage:
  python scripts/import_ai_training_data.py [--files path1 path2 ...] [--limit N] [--commit]

By default this performs a dry-run and will print counts. Use `--commit` to persist rows.
"""
import argparse
import json
import os
import sys
from datetime import datetime

from shapely.geometry import Polygon

# Ensure project root is first on sys.path so local `app.py` is imported
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from models import db, LandApplication, LandParcel, LandConflict
from geoalchemy2.shape import from_shape

# Create a minimal Flask app here using the project's DATABASE_URL so we don't
# import the top-level `app.py` (which pulls many optional dependencies).
from flask import Flask
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://user:pw@localhost/dbname')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with this app
db.init_app(app)


def parse_record(rec):
    # Map JSON keys to model fields
    application = LandApplication(
        reference_number=rec.get('reference_number') or rec.get('id'),
        applicant_name=rec.get('applicant_name') or 'Unknown',
        nrc_number=str(rec.get('nrc') or ''),
        tpin_number=str(rec.get('tpin') or ''),
        phone_number=str(rec.get('phone') or ''),
        email=rec.get('email') or '',
        land_location=rec.get('location') or rec.get('area') or '',
        land_size=float(rec.get('size_hectares') or rec.get('land_size') or 0.0),
        land_use=rec.get('land_use') or 'unknown',
        land_description=rec.get('land_description') or None,
        declared_value=rec.get('declared_value') or 0.0,
        status=rec.get('status') or 'pending',
        priority=rec.get('priority') or 'medium',
        registration_type=rec.get('registration_type') or 'title_issue',
        ai_processed=bool(rec.get('ai_processed', False)),
    )

    # parse submitted_at if present
    dt = rec.get('submitted_at')
    if dt:
        try:
            application.submitted_at = datetime.fromisoformat(dt)
        except Exception:
            pass

    # coordinates -> Polygon
    coords = rec.get('coordinates')
    parcel_geom = None
    if coords and isinstance(coords, list) and len(coords) >= 3:
        try:
            # JSON uses [lon, lat] pairs; shapely expects same ordering
            polygon = Polygon(coords)
            parcel_geom = from_shape(polygon, srid=4326)
            application.coordinates = parcel_geom
        except Exception:
            parcel_geom = None

    return application, parcel_geom


def main(files, limit=None, commit=False, create_conflicts=False):
    imported = 0
    skipped = 0
    created_app_ids = []

    with app.app_context():
        for path in files:
            if not os.path.exists(path):
                print('File not found:', path)
                continue

            with open(path, 'r', encoding='utf-8') as fh:
                try:
                    data = json.load(fh)
                except Exception as e:
                    print('Failed to parse JSON', path, e)
                    continue

            for i, rec in enumerate(data):
                if limit and imported >= limit:
                    break

                try:
                    application, parcel_geom = parse_record(rec)

                    # ensure unique reference_number
                    exists = LandApplication.query.filter_by(reference_number=application.reference_number).first()
                    if exists:
                        skipped += 1
                        continue

                    if commit:
                        db.session.add(application)
                        db.session.flush()  # get id

                        # create parcel linked to application
                        parcel_number = rec.get('plot_number') or f'PN-{application.reference_number}'
                        parcel = LandParcel(
                            parcel_number=str(parcel_number),
                            owner_name=application.applicant_name,
                            owner_nrc=application.nrc_number,
                            owner_phone=application.phone_number,
                            owner_email=application.email,
                            size=application.land_size,
                            location=application.land_location,
                            land_use=application.land_use,
                            application_id=application.id,
                            registered_at=application.submitted_at,
                        )
                        if parcel_geom is not None:
                            parcel.coordinates = parcel_geom

                        db.session.add(parcel)

                        # optionally create LandConflict rows for records that indicate a conflict
                        if create_conflicts and rec.get('has_conflict'):
                            cf = LandConflict(
                                application_id=application.id,
                                conflicting_parcel_id=None,
                                description=f"Imported conflict: {rec.get('conflict_type')}",
                                conflict_type=rec.get('conflict_type'),
                                title=f"Imported conflict for {application.reference_number}",
                                severity=rec.get('priority') or 'medium',
                                overlap_percentage=None,
                                confidence_score=0.5,
                                detected_by_ai=True
                            )
                            db.session.add(cf)

                        db.session.commit()
                        imported += 1
                        created_app_ids.append(application.id)
                    else:
                        # dry-run: just count
                        imported += 1

                except Exception as e:
                    print('Error importing record', getattr(rec, 'get', lambda x: None)('id'), e)
                    try:
                        db.session.rollback()
                    except Exception:
                        pass

    print('Files processed:', files)
    print('Imported (count):', imported)
    print('Skipped (existing refs):', skipped)
    if commit:
        print('Created application IDs sample:', created_app_ids[:10])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--files', nargs='*', help='JSON files to import (default: ai_training_data/*.json)')
    p.add_argument('--limit', type=int, help='Maximum number of records to import')
    p.add_argument('--commit', action='store_true', help='Persist changes to the DB (default is dry-run)')
    p.add_argument('--create-conflicts', action='store_true', help='Also create LandConflict rows for records with has_conflict')
    args = p.parse_args()

    if not args.files:
        base = os.path.join(os.path.dirname(__file__), '..', 'ai_training_data')
        base = os.path.abspath(base)
        files = [os.path.join(base, 'training_data.json'), os.path.join(base, 'test_data.json')]
    else:
        files = args.files

    main(files, limit=args.limit, commit=args.commit, create_conflicts=args.create_conflicts)
