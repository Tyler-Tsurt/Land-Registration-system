"""
duplicate_detector.py

Advanced duplicate detection system that checks for duplicates across different formats.
Detects:
1. Exact file duplicates (same hash)
2. Content duplicates (same person/property info in different file formats)
3. Identity duplicates (same NRC/TPIN across different applications)
4. Spatial duplicates (overlapping land parcels)
"""
import re
import hashlib
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from difflib import SequenceMatcher

from models import db, Document, LandApplication, LandParcel, LandConflict
from document_processing import extract_document_text
from validation_utils import normalize_identifier


def extract_identifiers_from_text(text: str) -> Dict[str, List[str]]:
    """
    Extract NRC numbers, TPINs, phone numbers, and emails from document text.
    
    Returns:
        Dict with keys: 'nrc', 'tpin', 'phone', 'email'
    """
    identifiers = {
        'nrc': [],
        'tpin': [],
        'phone': [],
        'email': []
    }
    
    if not text:
        return identifiers
    
    # Extract NRC numbers (format: 123456/12/1)
    nrc_pattern = r'\b\d{6}/\d{2}/\d\b'
    identifiers['nrc'] = list(set(re.findall(nrc_pattern, text)))
    
    # Extract TPIN numbers (10 digits)
    tpin_pattern = r'\b[1-9]\d{9}\b'
    identifiers['tpin'] = list(set(re.findall(tpin_pattern, text)))
    
    # Extract phone numbers (Zambian format)
    phone_pattern = r'(?:\+260|0)(?:95|96|97|76|77|75|78)\d{7}'
    identifiers['phone'] = list(set(re.findall(phone_pattern, text)))
    
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    identifiers['email'] = list(set(re.findall(email_pattern, text)))
    
    return identifiers


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity ratio between two texts using SequenceMatcher.
    
    Returns:
        Similarity ratio between 0.0 and 1.0
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    text1_norm = text1.lower().strip()
    text2_norm = text2.lower().strip()
    
    # Calculate similarity
    return SequenceMatcher(None, text1_norm, text2_norm).ratio()


def check_file_hash_duplicate(file_hash: str, exclude_doc_id: Optional[int] = None) -> List[Document]:
    """
    Check if a file with the same hash already exists.
    
    Args:
        file_hash: SHA-256 hash of the file
        exclude_doc_id: Document ID to exclude from search (for updates)
    
    Returns:
        List of duplicate documents
    """
    query = Document.query.filter(Document.file_hash == file_hash)
    
    if exclude_doc_id:
        query = query.filter(Document.id != exclude_doc_id)
    
    return query.all()


def check_content_duplicate(application_id: int) -> List[Dict]:
    """
    Check if application contains documents with content matching other applications.
    This detects cases where the same information is submitted in different file formats.
    
    Returns:
        List of conflict dictionaries with details
    """
    conflicts = []
    
    try:
        # Get current application and its documents
        application = LandApplication.query.get(application_id)
        if not application or not application.documents:
            return conflicts
        
        # Extract text and identifiers from all documents
        app_texts = []
        app_identifiers = {
            'nrc': set(),
            'tpin': set(),
            'phone': set(),
            'email': set()
        }
        
        for doc in application.documents:
            text = extract_document_text(doc.file_path, doc.mime_type)
            if text:
                app_texts.append(text)
                # Extract identifiers
                ids = extract_identifiers_from_text(text)
                for key in app_identifiers:
                    app_identifiers[key].update(ids[key])
        
        # Add application's own identifiers
        if application.nrc_number:
            app_identifiers['nrc'].add(normalize_identifier(application.nrc_number, 'nrc'))
        if application.tpin_number:
            app_identifiers['tpin'].add(normalize_identifier(application.tpin_number, 'tpin'))
        if application.phone_number:
            app_identifiers['phone'].add(normalize_identifier(application.phone_number, 'phone'))
        if application.email:
            app_identifiers['email'].add(normalize_identifier(application.email, 'email'))
        
        # Check against other applications
        other_applications = LandApplication.query.filter(
            LandApplication.id != application_id,
            LandApplication.user_id.isnot(None)
        ).all()
        
        for other_app in other_applications:
            match_score = 0.0
            match_details = []
            
            # Check identifier matches
            other_identifiers = {
                'nrc': set(),
                'tpin': set(),
                'phone': set(),
                'email': set()
            }
            
            if other_app.nrc_number:
                other_identifiers['nrc'].add(normalize_identifier(other_app.nrc_number, 'nrc'))
            if other_app.tpin_number:
                other_identifiers['tpin'].add(normalize_identifier(other_app.tpin_number, 'tpin'))
            if other_app.phone_number:
                other_identifiers['phone'].add(normalize_identifier(other_app.phone_number, 'phone'))
            if other_app.email:
                other_identifiers['email'].add(normalize_identifier(other_app.email, 'email'))
            
            # Extract from documents
            for doc in other_app.documents:
                text = extract_document_text(doc.file_path, doc.mime_type)
                if text:
                    ids = extract_identifiers_from_text(text)
                    for key in other_identifiers:
                        other_identifiers[key].update(ids[key])
            
            # Calculate matches
            for key in ['nrc', 'tpin', 'phone', 'email']:
                common = app_identifiers[key].intersection(other_identifiers[key])
                if common:
                    if key == 'nrc' or key == 'tpin':
                        match_score += 0.4  # High weight for ID numbers
                    elif key == 'email':
                        match_score += 0.2  # Medium weight
                    else:
                        match_score += 0.1  # Lower weight for phone
                    
                    match_details.append(f"Matching {key.upper()}: {', '.join(common)}")
            
            # If significant match found, create conflict
            if match_score >= 0.4:  # Threshold: at least one ID match
                conflicts.append({
                    'conflicting_app_id': other_app.id,
                    'conflict_type': 'content_duplicate',
                    'confidence_score': min(match_score, 1.0),
                    'details': match_details,
                    'other_app': other_app
                })
    
    except Exception as e:
        print(f"Error in check_content_duplicate: {e}")
        import traceback
        traceback.print_exc()
    
    return conflicts


def check_identity_duplicate(nrc: str, tpin: str, exclude_app_id: Optional[int] = None) -> List[LandApplication]:
    """
    Check if NRC or TPIN already exists in other applications.
    
    Args:
        nrc: NRC number to check
        tpin: TPIN number to check
        exclude_app_id: Application ID to exclude from search
    
    Returns:
        List of applications with matching identifiers
    """
    duplicates = []
    
    # Normalize identifiers
    nrc_norm = normalize_identifier(nrc, 'nrc') if nrc else None
    tpin_norm = normalize_identifier(tpin, 'tpin') if tpin else None
    
    # Build query
    query = LandApplication.query.filter(LandApplication.user_id.isnot(None))
    
    if exclude_app_id:
        query = query.filter(LandApplication.id != exclude_app_id)
    
    # Check NRC matches
    if nrc_norm:
        nrc_matches = query.filter(LandApplication.nrc_number == nrc_norm).all()
        duplicates.extend(nrc_matches)
    
    # Check TPIN matches
    if tpin_norm:
        tpin_matches = query.filter(LandApplication.tpin_number == tpin_norm).all()
        # Avoid adding duplicates if already matched by NRC
        for match in tpin_matches:
            if match not in duplicates:
                duplicates.append(match)
    
    return duplicates


def detect_all_duplicates(application_id: int) -> List[LandConflict]:
    """
    Comprehensive duplicate detection for an application.
    Checks:
    1. File hash duplicates
    2. Content duplicates across formats
    3. Identity duplicates (NRC/TPIN)
    
    Returns:
        List of created LandConflict objects
    """
    created_conflicts = []
    
    try:
        application = LandApplication.query.get(application_id)
        if not application:
            return created_conflicts
        
        # 1. Check file hash duplicates
        for doc in application.documents:
            if doc.file_hash:
                hash_duplicates = check_file_hash_duplicate(doc.file_hash, doc.id)
                
                for dup_doc in hash_duplicates:
                    # Only create conflict if from different application
                    if dup_doc.application_id != application_id:
                        dup_app = dup_doc.application
                        
                        # Check if conflict already exists
                        existing = LandConflict.query.filter_by(
                            application_id=application_id,
                            conflict_type='document_duplicate',
                            status='unresolved'
                        ).filter(
                            LandConflict.description.like(f'%{dup_app.reference_number}%')
                        ).first()
                        
                        if not existing:
                            conflict = LandConflict(
                                application_id=application_id,
                                conflicting_parcel_id=dup_app.land_parcel.id if dup_app.land_parcel else None,
                                description=build_duplicate_description('document', doc, dup_doc, dup_app),
                                status='unresolved',
                                detected_by_ai=True,
                                created_at=datetime.utcnow(),
                                conflict_type='document_duplicate',
                                title=f"⚠️ Duplicate Document: {doc.document_type}",
                                severity='high',
                                confidence_score=1.0  # Exact hash match = 100% confidence
                            )
                            db.session.add(conflict)
                            created_conflicts.append(conflict)
        
        # 2. Check content duplicates
        content_conflicts = check_content_duplicate(application_id)
        
        for conflict_data in content_conflicts:
            # Check if conflict already exists
            existing = LandConflict.query.filter_by(
                application_id=application_id,
                conflict_type='content_duplicate',
                status='unresolved'
            ).filter(
                LandConflict.description.like(f'%{conflict_data["other_app"].reference_number}%')
            ).first()
            
            if not existing:
                other_app = conflict_data['other_app']
                conflict = LandConflict(
                    application_id=application_id,
                    conflicting_parcel_id=other_app.land_parcel.id if other_app.land_parcel else None,
                    description=build_content_duplicate_description(application, other_app, conflict_data['details']),
                    status='unresolved',
                    detected_by_ai=True,
                    created_at=datetime.utcnow(),
                    conflict_type='content_duplicate',
                    title=f"⚠️ Content Duplicate with Application {other_app.reference_number}",
                    severity='high',
                    confidence_score=conflict_data['confidence_score']
                )
                db.session.add(conflict)
                created_conflicts.append(conflict)
        
        # 3. Check identity duplicates
        identity_duplicates = check_identity_duplicate(
            application.nrc_number,
            application.tpin_number,
            application_id
        )
        
        for dup_app in identity_duplicates:
            # Check if conflict already exists
            existing = LandConflict.query.filter_by(
                application_id=application_id,
                conflict_type='identity_duplicate',
                status='unresolved'
            ).filter(
                LandConflict.description.like(f'%{dup_app.reference_number}%')
            ).first()
            
            if not existing:
                conflict = LandConflict(
                    application_id=application_id,
                    conflicting_parcel_id=dup_app.land_parcel.id if dup_app.land_parcel else None,
                    description=build_identity_duplicate_description(application, dup_app),
                    status='unresolved',
                    detected_by_ai=True,
                    created_at=datetime.utcnow(),
                    conflict_type='identity_duplicate',
                    title=f"⚠️ Same Person/Entity: {dup_app.applicant_name}",
                    severity='medium',
                    confidence_score=0.95
                )
                db.session.add(conflict)
                created_conflicts.append(conflict)
        
        if created_conflicts:
            application.ai_processed = True
            application.status = 'conflict'
            db.session.commit()
    
    except Exception as e:
        db.session.rollback()
        print(f"Error in detect_all_duplicates: {e}")
        import traceback
        traceback.print_exc()
    
    return created_conflicts


def build_duplicate_description(dup_type: str, doc1: Document, doc2: Document, other_app: LandApplication) -> str:
    """Build detailed description for document duplicate."""
    lines = []
    lines.append("🚨 EXACT DOCUMENT DUPLICATE DETECTED")
    lines.append("\nAI has detected that you uploaded the EXACT SAME FILE that exists in another application.")
    lines.append("\n📄 YOUR DOCUMENT:")
    lines.append(f"• Filename: {doc1.original_filename}")
    lines.append(f"• Type: {doc1.document_type}")
    lines.append(f"• Size: {doc1.file_size // 1024} KB")
    lines.append(f"• Upload Date: {doc1.uploaded_at.strftime('%Y-%m-%d %H:%M')}")
    lines.append("\n🔄 MATCHING DOCUMENT FROM:")
    lines.append(f"• Application: {other_app.reference_number}")
    lines.append(f"• Applicant: {other_app.applicant_name}")
    lines.append(f"• NRC: {other_app.nrc_number}")
    lines.append(f"• Location: {other_app.land_location}")
    lines.append(f"• Date: {other_app.submitted_at.strftime('%Y-%m-%d')}")
    lines.append(f"• Document: {doc2.original_filename}")
    lines.append(f"• Type: {doc2.document_type}")
    lines.append("\n⚠️ SEVERITY: CRITICAL")
    lines.append("This is a 100% exact match (same file hash).")
    lines.append("\n❓ POSSIBLE CAUSES:")
    lines.append("• Same person applying twice (Check if both applications are yours)")
    lines.append("• Document accidentally reused from another application")
    lines.append("• Someone else uploaded your document without permission")
    lines.append("• Fraudulent activity (using someone else's documents)")
    lines.append("\n✅ REQUIRED ACTION:")
    lines.append("1. Contact the registry IMMEDIATELY if you did not create both applications")
    lines.append("2. Provide written explanation if this is a legitimate resubmission")
    lines.append("3. Upload NEW, ORIGINAL documents if this was an error")
    
    return "\n".join(lines)


def build_content_duplicate_description(app1: LandApplication, app2: LandApplication, details: List[str]) -> str:
    """Build detailed description for content duplicate."""
    lines = []
    lines.append("🔍 CONTENT DUPLICATE DETECTED")
    lines.append("\nAI has found that your application contains information matching another application.")
    lines.append("This may indicate the same person/property submitted in different file formats.")
    lines.append("\n📋 MATCHING INFORMATION:")
    for detail in details:
        lines.append(f"• {detail}")
    lines.append("\n📃 CONFLICTING APPLICATION:")
    lines.append(f"• Reference: {app2.reference_number}")
    lines.append(f"• Applicant: {app2.applicant_name}")
    lines.append(f"• NRC: {app2.nrc_number}")
    lines.append(f"• TPIN: {app2.tpin_number}")
    lines.append(f"• Location: {app2.land_location}")
    lines.append(f"• Date Submitted: {app2.submitted_at.strftime('%Y-%m-%d')}")
    lines.append(f"• Status: {app2.status.upper()}")
    lines.append("\n⚠️ WHY THIS MATTERS:")
    lines.append("• You cannot apply for land twice using the same identity")
    lines.append("• Each person can only have ONE active application per property")
    lines.append("• This could be fraudulent use of your identity")
    lines.append("\n✅ WHAT TO DO:")
    lines.append("1. If BOTH applications are yours:")
    lines.append("   - Contact registry to withdraw one application")
    lines.append("   - Explain why you submitted twice")
    lines.append("2. If the OTHER application is NOT yours:")
    lines.append("   - Report immediately - someone may be using your identity")
    lines.append("   - Bring your ID to the registry for verification")
    lines.append("3. If this is a mistake:")
    lines.append("   - Provide documentation showing different identity")
    
    return "\n".join(lines)


def build_identity_duplicate_description(app1: LandApplication, app2: LandApplication) -> str:
    """Build detailed description for identity duplicate."""
    lines = []
    lines.append("👤 SAME IDENTITY DETECTED")
    lines.append("\nYour NRC and/or TPIN matches another application in the system.")
    lines.append("\n📇 YOUR APPLICATION:")
    lines.append(f"• Reference: {app1.reference_number}")
    lines.append(f"• Applicant: {app1.applicant_name}")
    lines.append(f"• NRC: {app1.nrc_number}")
    lines.append(f"• TPIN: {app1.tpin_number}")
    lines.append(f"• Location: {app1.land_location}")
    lines.append("\n🔄 EXISTING APPLICATION:")
    lines.append(f"• Reference: {app2.reference_number}")
    lines.append(f"• Applicant: {app2.applicant_name}")
    lines.append(f"• NRC: {app2.nrc_number}")
    lines.append(f"• TPIN: {app2.tpin_number}")
    lines.append(f"• Location: {app2.land_location}")
    lines.append(f"• Date: {app2.submitted_at.strftime('%Y-%m-%d')}")
    lines.append(f"• Status: {app2.status.upper()}")
    lines.append("\n⚠️ POLICY:")
    lines.append("• Each person can only have ONE active land application")
    lines.append("• You must withdraw one application to proceed with the other")
    lines.append("• Both applications will be on hold until resolved")
    lines.append("\n✅ RESOLUTION:")
    lines.append("1. Visit the registry with your National ID")
    lines.append("2. Choose which application to keep")
    lines.append("3. Formally withdraw the other application")
    lines.append("4. Alternatively, combine both into one application if for different properties")
    
    return "\n".join(lines)
