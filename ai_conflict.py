"""
ai_conflict.py

Pluggable AI conflict detection & resolution helpers.

Design:
- detect_conflicts(application_id) -> list of created LandConflict records (or empty list)
- resolve_conflict(conflict_id, action, resolved_by=None) -> updates record and returns it

This module uses a safe local heuristic by default (string matching, owner duplicates,
and geometric intersection via geoalchemy2->shapely when geometries exist). It is
designed to be pluggable so an external ML/LLM provider can be added later.
"""
from datetime import datetime
import math
import logging

import sys


from geoalchemy2.shape import to_shape
from shapely.geometry import shape

from models import db, LandApplication, LandParcel, LandConflict, AuditLog






# Enable debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)





logger = logging.getLogger(__name__)


def detect_conflicts(application_id):
    """Detect potential conflicts for an application.

    Returns: list of LandConflict objects (persisted) created for this application.
    The function will:
    - load the application
    - run simple heuristics (owner nrc duplicates, location substring match)
    - if geometries exist, use spatial intersection to compute overlap % and confidence
    - create LandConflict rows with metadata and a confidence_score
    """
    created = []
    try:
        print(f"[ai_conflict] detect_conflicts START for application_id={application_id}")
        application = db.session.get(LandApplication, application_id)
        if not application:
            print(f"[ai_conflict] application {application_id} not found")
            return created

        # Basic heuristics
        candidates = []

        # 1) Owner NRC duplicates (same NRC found in existing parcels)
        if application.nrc_number:
            dup_parcels = LandParcel.query.filter(LandParcel.owner_nrc == application.nrc_number).all()
            print(f"[ai_conflict] owner duplicate search found {len(dup_parcels)} parcels for nrc={application.nrc_number}")
            for p in dup_parcels:
                candidates.append((p, 'owner_duplicate', 0.6))

        # 2) Location textual match (substring)
        if application.land_location:
            text_matches = LandParcel.query.filter(LandParcel.location.ilike(f"%{application.land_location}%"))
            text_matches_list = list(text_matches)
            print(f"[ai_conflict] location text search found {len(text_matches_list)} parcels for location='{application.land_location}'")
            for p in text_matches_list:
                candidates.append((p, 'location_match', 0.4))

        # 3) Spatial intersection using shapely if possible
        app_geom = None
        try:
            if application.coordinates is not None:
                app_geom = to_shape(application.coordinates)
            else:
                logger.warning('Application %s has no coordinates for spatial analysis', application_id)
        except Exception as e:
            logger.error('Failed to parse geometry for application %s: %s', application_id, e)
            app_geom = None

        if app_geom:
            print(f"[ai_conflict] Application has geometry; running spatial checks")
            parcels = LandParcel.query.filter(LandParcel.coordinates != None).all()
            for p in parcels:
                try:
                    if p.coordinates is None:
                        continue
                    parcel_geom = to_shape(p.coordinates)
                    if parcel_geom.intersects(app_geom):
                        inter = parcel_geom.intersection(app_geom)
                        # compute overlap relative to parcel area
                        overlap_pct = 0.0
                        try:
                            if parcel_geom.area > 0:
                                overlap_pct = float(inter.area / parcel_geom.area)
                        except Exception:
                            overlap_pct = 0.0

                        # confidence increases with overlap percentage
                        confidence = min(0.95, 0.2 + overlap_pct * 0.9)
                        candidates.append((p, 'spatial_overlap', confidence, overlap_pct))
                        print(f"[ai_conflict] spatial overlap with parcel id={p.id} overlap_pct={overlap_pct} confidence={confidence}")
                except Exception:
                    logger.exception('Error processing parcel geometry id=%s', getattr(p, 'id', None))

        # Deduplicate candidates by parcel id and pick the highest-confidence reason
        best = {}
        for entry in candidates:
            parcel = entry[0]
            reason = entry[1]
            confidence = entry[2]
            overlap_pct = entry[3] if len(entry) > 3 else None
            pid = parcel.id
            prev = best.get(pid)
            score = confidence
            if prev is None or score > prev['confidence']:
                best[pid] = {
                    'parcel': parcel,
                    'reason': reason,
                    'confidence': score,
                    'overlap_pct': overlap_pct
                }

        # Persist LandConflict rows
        for pid, info in best.items():
            # skip very low confidence (lowered threshold to catch more conflicts)
            if info['confidence'] < 0.15:
                continue

            parcel = info['parcel']
            reason = info['reason']
            confidence = info['confidence']
            overlap_pct = info.get('overlap_pct')
            
            # Build detailed description based on conflict type
            details = []
            
            if reason == 'spatial_overlap':
                details.append(f"⚠️ GEOGRAPHIC OVERLAP DETECTED")
                details.append(f"\nThe boundaries of this application physically overlap with an existing registered parcel.")
                details.append(f"\n📍 Conflicting Parcel: {parcel.parcel_number}")
                details.append(f"👤 Current Owner: {parcel.owner_name or 'Unknown'}")
                details.append(f"📞 Owner Phone: {parcel.owner_phone or 'N/A'}")
                details.append(f"📧 Owner Email: {parcel.owner_email or 'N/A'}")
                if overlap_pct:
                    details.append(f"\n📊 Overlap Percentage: {overlap_pct * 100:.2f}% of the existing parcel")
                details.append(f"📐 Parcel Size: {parcel.size or 'N/A'} hectares")
                details.append(f"📍 Parcel Location: {parcel.location or 'N/A'}")
                details.append(f"\n🔍 WHAT THIS MEANS:")
                details.append(f"- Your application boundaries overlap with land already registered to {parcel.owner_name or 'another person'}")
                details.append(f"- This could be a boundary error, survey mistake, or potential land dispute")
                details.append(f"\n✅ REQUIRED ACTIONS:")
                details.append(f"1. Verify your land boundaries are correct")
                details.append(f"2. Check if you have proof of ownership for this specific area")
                details.append(f"3. Contact {parcel.owner_name or 'the registered owner'} if this is a known boundary adjustment")
                details.append(f"4. Provide updated survey documents showing correct boundaries")
                
            elif reason == 'owner_duplicate':
                details.append(f"⚠️ DUPLICATE OWNER NRC DETECTED")
                details.append(f"\nThe same National Registration Card (NRC) number is already associated with another parcel.")
                details.append(f"\n📍 Existing Parcel: {parcel.parcel_number}")
                details.append(f"👤 Owner Name on Record: {parcel.owner_name or 'Unknown'}")
                details.append(f"🆔 NRC Number: {application.nrc_number}")
                details.append(f"📍 Existing Parcel Location: {parcel.location or 'N/A'}")
                details.append(f"📐 Existing Parcel Size: {parcel.size or 'N/A'} hectares")
                details.append(f"\n🔍 WHAT THIS MEANS:")
                details.append(f"- You already have a registered parcel in the system")
                details.append(f"- This might be a legitimate second parcel registration")
                details.append(f"- Or this could be a correction/update to your existing parcel")
                details.append(f"\n✅ REQUIRED ACTIONS:")
                details.append(f"1. Confirm this is a NEW parcel (not an update to parcel {parcel.parcel_number})")
                details.append(f"2. If updating existing parcel, please contact the registry office")
                details.append(f"3. Provide proof this is a separate land acquisition")
                details.append(f"4. Ensure all documentation shows the new parcel location clearly")
                
            elif reason == 'location_match':
                details.append(f"⚠️ SIMILAR LOCATION DETECTED")
                details.append(f"\nYour application location matches or is very similar to an existing parcel location.")
                details.append(f"\n📍 Your Location: {application.land_location}")
                details.append(f"📍 Existing Parcel: {parcel.parcel_number}")
                details.append(f"📍 Existing Location: {parcel.location or 'N/A'}")
                details.append(f"👤 Current Owner: {parcel.owner_name or 'Unknown'}")
                details.append(f"📐 Parcel Size: {parcel.size or 'N/A'} hectares")
                details.append(f"\n🔍 WHAT THIS MEANS:")
                details.append(f"- The location description you provided matches an existing registration")
                details.append(f"- This could be the same plot/area or adjacent property")
                details.append(f"\n✅ REQUIRED ACTIONS:")
                details.append(f"1. Verify your location description is accurate and specific")
                details.append(f"2. Provide more details to distinguish your parcel (street number, plot number)")
                details.append(f"3. Confirm you're not attempting to register the same land as parcel {parcel.parcel_number}")
                details.append(f"4. Submit updated location information if there was an error")
            
            description = "\n".join(details)
            
            title = f"⚠️ {reason.replace('_', ' ').title()}: {parcel.parcel_number}"
            
            conflict = LandConflict(
                application_id=application.id,
                conflicting_parcel_id=info['parcel'].id,
                description=description,
                detected_by_ai=True,
                conflict_type=info['reason'],
                title=title,
                severity='medium' if info['confidence'] < 0.7 else 'high',
                overlap_percentage=info.get('overlap_pct'),
                confidence_score=info['confidence']
            )
            db.session.add(conflict)
            created.append(conflict)
            print(f"[ai_conflict] created conflict candidate for parcel id={info['parcel'].id} reason={info['reason']} confidence={info['confidence']}")

        # mark application as processed and set best scores
        if created:
            # pick highest confidence
            best_conf = max(c.confidence_score for c in created if c.confidence_score is not None)
            application.ai_conflict_score = best_conf
            application.ai_processed = True
            application.status = 'conflict'
        else:
            application.ai_processed = True
            application.ai_conflict_score = 0.0

        db.session.commit()
        # refresh objects
        for c in created:
            db.session.refresh(c)

        # audit
        try:
            log_audit('ai_detect_conflicts', 'land_applications', application.id, new_values={'created_conflicts': [c.id for c in created]})
        except Exception:
            db.session.rollback()

        print(f"[ai_conflict] detect_conflicts END for application_id={application_id} created={len(created)}")
        return created

    except Exception as e:
        # Print and re-raise to make test failures visible
        print(f"[ai_conflict] ERROR detect_conflicts for application {application_id}: {e}")
        logger.exception('Failed to detect conflicts for application %s: %s', application_id, e)
        db.session.rollback()
        raise


def log_audit(action, table_name, record_id, old_values=None, new_values=None):
    """Logs an audit event to the AuditLog model."""
    try:
        audit_log = AuditLog(
            user_id=None,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            timestamp=datetime.utcnow()
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception:
        # If audit logging fails, don't break the main flow.
        logger.exception("Failed to write audit log")


def resolve_conflict(conflict_id, action='mark_resolved', resolved_by=None):
    """Resolve a conflict record.

    action: 'mark_resolved' or custom
    resolved_by: user id
    Returns the updated LandConflict or None
    """
    try:
        conflict = db.session.get(LandConflict, conflict_id)
        if not conflict:
            return None
        old = {
            'status': conflict.status,
            'resolved_at': conflict.resolved_at
        }
        conflict.status = 'resolved'
        conflict.resolved_at = datetime.utcnow()
        db.session.commit()

        # audit log
        try:
            log = AuditLog(user_id=resolved_by, action='resolve_conflict', table_name='land_conflicts', record_id=conflict.id, old_values=old, new_values={'status': 'resolved'})
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        return conflict
    except Exception:
        logger.exception('Failed to resolve conflict %s', conflict_id)
        db.session.rollback()
        return None
