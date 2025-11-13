"""
Test AI Conflict Detection System

This script tests all three AI detection methods:
1. Spatial conflicts (overlapping land parcels)
2. Document similarity (duplicate documents)
3. Identity duplicates (same person applying twice)

Usage: python test_ai_system.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, LandApplication, LandConflict, User
from ai_conflict import detect_conflicts
from ai_conflict_enhanced import detect_conflicts_from_documents
from duplicate_detector import detect_all_duplicates


def test_single_application(app_id):
    """Test AI detection for a single application."""
    print(f"\n{'='*70}")
    print(f"TESTING APPLICATION ID: {app_id}")
    print(f"{'='*70}")
    
    with app.app_context():
        # Get application details
        application = db.session.get(LandApplication, app_id)
        if not application:
            print(f"❌ Application {app_id} not found!")
            return
        
        print(f"\n📋 Application Details:")
        print(f"   Reference: {application.reference_number}")
        print(f"   Applicant: {application.applicant_name}")
        print(f"   NRC: {application.nrc_number}")
        print(f"   TPIN: {application.tpin_number}")
        print(f"   Location: {application.land_location}")
        print(f"   Status: {application.status}")
        print(f"   Documents: {len(application.documents)}")
        
        # Test 1: Spatial Conflicts
        print(f"\n🗺️  TEST 1: Spatial Conflict Detection")
        print(f"   {'.'*60}")
        try:
            spatial = detect_conflicts(app_id)
            print(f"   ✅ Found {len(spatial)} spatial conflicts")
            for i, conflict in enumerate(spatial, 1):
                print(f"      {i}. Type: {conflict.conflict_type}")
                print(f"         Confidence: {conflict.confidence_score*100:.1f}%")
                if conflict.overlap_percentage:
                    print(f"         Overlap: {conflict.overlap_percentage*100:.2f}%")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: Document Similarity
        print(f"\n📄 TEST 2: Document Similarity Detection")
        print(f"   {'.'*60}")
        try:
            docs = detect_conflicts_from_documents(app_id)
            print(f"   ✅ Found {len(docs)} document conflicts")
            for i, conflict in enumerate(docs, 1):
                print(f"      {i}. Type: {conflict.conflict_type}")
                print(f"         Confidence: {conflict.confidence_score*100:.1f}%")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: Duplicate Detection
        print(f"\n🔍 TEST 3: Comprehensive Duplicate Detection")
        print(f"   {'.'*60}")
        try:
            dups = detect_all_duplicates(app_id)
            print(f"   ✅ Found {len(dups)} duplicate conflicts")
            
            # Categorize duplicates
            by_type = {}
            for conflict in dups:
                t = conflict.conflict_type
                by_type[t] = by_type.get(t, 0) + 1
            
            for conflict_type, count in by_type.items():
                print(f"      - {conflict_type}: {count}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Summary
        print(f"\n📊 SUMMARY")
        print(f"   {'='*60}")
        all_conflicts = LandConflict.query.filter_by(application_id=app_id).all()
        print(f"   Total Conflicts in Database: {len(all_conflicts)}")
        
        if all_conflicts:
            print(f"\n   Conflict Breakdown:")
            conflict_summary = {}
            for c in all_conflicts:
                t = c.conflict_type or 'unknown'
                conflict_summary[t] = conflict_summary.get(t, 0) + 1
            
            for c_type, count in conflict_summary.items():
                print(f"      - {c_type}: {count}")
        
        print(f"\n   Application Status: {application.status}")
        print(f"   AI Processed: {'✅ Yes' if application.ai_processed else '❌ No'}")


def test_all_applications():
    """Test AI detection for all applications."""
    print(f"\n{'='*70}")
    print(f"TESTING ALL APPLICATIONS")
    print(f"{'='*70}")
    
    with app.app_context():
        # FIXED: Changed 'app' to 'application' to avoid shadowing
        applications = LandApplication.query.filter(
            LandApplication.user_id.isnot(None)
        ).all()
        
        print(f"\nFound {len(applications)} applications")
        
        for i, application in enumerate(applications, 1):
            print(f"\n[{i}/{len(applications)}] Testing {application.reference_number}...")
            try:
                test_single_application(application.id)
            except Exception as e:
                print(f"❌ Failed: {e}")
                import traceback
                traceback.print_exc()


def show_statistics():
    """Show AI detection statistics."""
    print(f"\n{'='*70}")
    print(f"AI DETECTION STATISTICS")
    print(f"{'='*70}")
    
    with app.app_context():
        # Application stats
        total_apps = LandApplication.query.filter(
            LandApplication.user_id.isnot(None)
        ).count()
        
        processed_apps = LandApplication.query.filter_by(
            ai_processed=True
        ).count()
        
        conflict_apps = LandApplication.query.filter_by(
            status='conflict'
        ).count()
        
        print(f"\n📊 Application Statistics:")
        print(f"   Total Applications: {total_apps}")
        print(f"   AI Processed: {processed_apps} ({processed_apps/total_apps*100 if total_apps > 0 else 0:.1f}%)")
        print(f"   With Conflicts: {conflict_apps} ({conflict_apps/total_apps*100 if total_apps > 0 else 0:.1f}%)")
        
        # Conflict stats
        total_conflicts = LandConflict.query.count()
        unresolved = LandConflict.query.filter_by(status='unresolved').count()
        resolved = LandConflict.query.filter_by(status='resolved').count()
        
        print(f"\n⚠️  Conflict Statistics:")
        print(f"   Total Conflicts: {total_conflicts}")
        print(f"   Unresolved: {unresolved}")
        print(f"   Resolved: {resolved}")
        
        # Conflict types
        conflict_types = db.session.query(
            LandConflict.conflict_type,
            db.func.count(LandConflict.id)
        ).group_by(LandConflict.conflict_type).all()
        
        print(f"\n🔍 Conflict Types:")
        for c_type, count in conflict_types:
            print(f"   - {c_type or 'unknown'}: {count}")
        
        # High confidence conflicts (potential fraud)
        high_conf = LandConflict.query.filter(
            LandConflict.confidence_score >= 0.85,
            LandConflict.status == 'unresolved'
        ).count()
        
        print(f"\n🚨 High Risk Alerts:")
        print(f"   High Confidence Conflicts (>85%): {high_conf}")


def main():
    """Main test function."""
    print(f"\n{'#'*70}")
    print(f"# AI CONFLICT DETECTION SYSTEM TEST")
    print(f"{'#'*70}")
    
    if len(sys.argv) > 1:
        # Test specific application
        try:
            app_id = int(sys.argv[1])
            test_single_application(app_id)
        except ValueError:
            print("❌ Invalid application ID. Must be a number.")
            sys.exit(1)
    else:
        # Show menu
        print("\nOptions:")
        print("  1. Test all applications")
        print("  2. Show statistics only")
        print("  3. Test specific application")
        print("  0. Exit")
        
        choice = input("\nEnter choice (1-3, 0 to exit): ").strip()
        
        if choice == '1':
            test_all_applications()
        elif choice == '2':
            show_statistics()
        elif choice == '3':
            app_id = input("Enter application ID: ").strip()
            try:
                test_single_application(int(app_id))
            except ValueError:
                print("❌ Invalid application ID")
        elif choice == '0':
            print("Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice")
            sys.exit(1)
    
    # Always show stats at the end
    show_statistics()
    
    print(f"\n{'#'*70}")
    print(f"# TEST COMPLETE")
    print(f"{'#'*70}\n")


if __name__ == '__main__':
    main()
