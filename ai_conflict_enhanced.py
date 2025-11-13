"""
ai_conflict_enhanced.py

Enhanced AI conflict detection using document content analysis.
"""
import logging
import os
import pickle
from collections import defaultdict
from datetime import datetime

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from document_processing import extract_document_text
from models import db, Document, LandApplication, LandConflict, AuditLog

logger = logging.getLogger(__name__)


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


def detect_conflicts_from_documents(application_id):
    """
    Detect potential conflicts for an application based on document content.

    - Extracts text from all documents in the new application.
    - Compares against documents from all other applications.
    - Uses TF-IDF and cosine similarity to find potential document duplicates.
    """
    try:
        application = LandApplication.query.get(application_id)
        if not application or not application.documents:
            logger.info(f"No documents found for application {application_id}")
            return []

        # 1. Extract text from the new application's documents
        new_docs_text = {}
        for doc in application.documents:
            text = extract_document_text(doc.file_path, doc.mime_type)
            if text:
                new_docs_text[doc.id] = text

        if not new_docs_text:
            logger.info(f"No text could be extracted from documents for application {application_id}")
            return []

        # 2. Get all documents from other applications
        other_docs = Document.query.filter(Document.application_id != application_id).all()
        if not other_docs:
            logger.info("No other documents in the system to compare against.")
            return []

        # 3. Group documents by application to avoid intra-application conflicts
        docs_by_app = defaultdict(list)
        for doc in other_docs:
            docs_by_app[doc.application_id].append(doc)

        # 4. Vectorize and compare
        vectorizer_path = 'tfidf_vectorizer.pkl'
        all_texts = list(new_docs_text.values()) + [extract_document_text(d.file_path, d.mime_type) for app_docs in
                                                    docs_by_app.values() for d in app_docs]
        
        if os.path.exists(vectorizer_path):
            with open(vectorizer_path, 'rb') as f:
                vectorizer = pickle.load(f)
            tfidf_matrix = vectorizer.transform(all_texts)
        else:
            vectorizer = TfidfVectorizer(stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(all_texts)

        # Split the matrix back into new_docs and other_docs
        num_new_docs = len(new_docs_text)
        new_docs_matrix = tfidf_matrix[:num_new_docs]
        other_docs_matrix = tfidf_matrix[num_new_docs:]

        # Calculate cosine similarity
        cosine_similarities = cosine_similarity(new_docs_matrix, other_docs_matrix)

        # 5. Identify conflicts
        conflicts = []
        other_docs_flat = [d for app_docs in docs_by_app.values() for d in app_docs]

        for i, new_doc_id in enumerate(new_docs_text.keys()):
            for j, similarity in enumerate(cosine_similarities[i]):
                if similarity > 0.8:  # Similarity threshold
                    conflicting_doc = other_docs_flat[j]
                    new_doc = Document.query.get(new_doc_id)
                    conflicting_app = conflicting_doc.application
                    
                    # Build detailed description
                    details = []
                    details.append(f"⚠️ DUPLICATE DOCUMENT DETECTED")
                    details.append(f"\nAI has detected that one of your documents is highly similar to a document from another application.")
                    details.append(f"\n📄 Your Document: {new_doc.original_filename}")
                    details.append(f"📂 Document Type: {new_doc.document_type}")
                    details.append(f"\n🔄 MATCHING DOCUMENT:")
                    details.append(f"📄 Conflicting Document: {conflicting_doc.original_filename}")
                    details.append(f"📂 Document Type: {conflicting_doc.document_type}")
                    details.append(f"📊 Similarity Score: {similarity * 100:.1f}%")
                    details.append(f"\n📃 FROM APPLICATION:")
                    details.append(f"📝 Reference: {conflicting_app.reference_number}")
                    details.append(f"👤 Applicant: {conflicting_app.applicant_name}")
                    details.append(f"🆔 NRC: {conflicting_app.nrc_number}")
                    details.append(f"📍 Location: {conflicting_app.land_location}")
                    details.append(f"📅 Submitted: {conflicting_app.submitted_at.strftime('%Y-%m-%d')}")
                    details.append(f"\n🔍 WHAT THIS MEANS:")
                    details.append(f"- The same or very similar document was uploaded for another application")
                    details.append(f"- This could indicate:")
                    details.append(f"  • Document reuse (same document used for multiple applications)")
                    details.append(f"  • Fraudulent activity (copying someone else's documents)")
                    details.append(f"  • Legitimate duplicate if you're the same person on both applications")
                    details.append(f"\n❗ SEVERITY: This is flagged as HIGH RISK due to {similarity * 100:.1f}% similarity")
                    details.append(f"\n✅ REQUIRED ACTIONS:")
                    details.append(f"1. Verify all documents you uploaded are YOUR original documents")
                    details.append(f"2. Check if you previously applied as '{conflicting_app.applicant_name}'")
                    details.append(f"3. If this is a legitimate duplicate, provide written explanation")
                    details.append(f"4. If documents were obtained fraudulently, this application will be rejected")
                    details.append(f"5. Contact the registry immediately if you believe this is an error")
                    
                    description = "\n".join(details)
                    
                    conflict = LandConflict(
                        application_id=application_id,
                        conflicting_parcel_id=conflicting_doc.application.land_parcel.id if conflicting_doc.application.land_parcel else None,
                        description=description,
                        status='unresolved',
                        detected_by_ai=True,
                        created_at=datetime.utcnow(),
                        conflict_type='document_duplicate',
                        title=f"⚠️ Document Duplicate: {new_doc.document_type}",
                        severity='high',
                        confidence_score=similarity
                    )
                    conflicts.append(conflict)
                    db.session.add(conflict)

        if conflicts:
            application.status = 'conflict'
            db.session.commit()
            try:
                log_audit('ai_detect_conflicts_from_documents', 'land_applications', application.id, new_values={'created_conflicts': [c.id for c in conflicts]})
            except Exception:
                db.session.rollback()

        return conflicts

    except Exception as e:
        logger.error(f"Error in detect_conflicts_from_documents for application {application_id}: {e}")
        db.session.rollback()
        return []