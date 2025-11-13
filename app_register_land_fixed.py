
@login_required
def register_land():
    """Handle land registration for citizens - FIXED VERSION"""
    if current_user.role != "citizen":
        flash("Only citizens can register land", "danger")
        return redirect(url_for("index"))

    if request.method == 'POST':
        try:
            # Generate reference number
            reference_number = f"LR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            # Get registration type and fees
            registration_type = request.form.get('registration_type')
            if not registration_type:
                flash('Please select a registration type', 'danger')
                return render_template('register_land.html')

            try:
                payment_amount = float(request.form.get('payment_amount', 0))
            except Exception:
                payment_amount = 0.0

            declared_value_raw = request.form.get('declared_value', '')
            declared_value = 0.0
            try:
                if declared_value_raw and declared_value_raw.strip() != '':
                    declared_value = float(declared_value_raw.replace(',',''))
            except Exception:
                flash('Declared value must be a valid number', 'danger')
                return render_template('register_land.html')

            # Document requirements per type
            doc_requirements = {
                'transfer': ['seller_id','buyer_id','seller_tpin','buyer_tpin','sale_agreement','current_title_deed'],
                'lease': ['offer_letter','lease_agreement','survey_map','proof_rent','nrc_copy','tpin_certificate'],
                'mortgage': ['mortgage_deed','lender_name_tpin','borrower_id','secured_amount'],
                'title_issue': ['offer_letter','survey_map','nrc_copy','tpin_certificate'],
                'subdivision': ['original_title_copy','survey_map','nrc_copy','application_letter'],
                'replacement': ['police_report','statutory_declaration','nrc_copy'],
                'change_ownership': ['assignment_deed','old_title_copy','seller_tpin','buyer_tpin','nrc_copy'],
                'caveat': ['caveat_document','nrc_copy','proof_of_interest']
            }

            required_keys = doc_requirements.get(registration_type, [])

            # Validate declared value for specific types
            needs_declared = registration_type in ('transfer','mortgage','change_ownership')
            if needs_declared and (not declared_value or declared_value <= 0):
                flash('Declared property value is required for this registration type', 'danger')
                return render_template('register_land.html')

            # Validate NRC
            nrc_number = (request.form.get('nrc_number') or '').strip()
            nrc_valid, nrc_error = validate_nrc(nrc_number)
            if not nrc_valid:
                # Try passport validation
                from validation_utils import validate_passport
                passport_valid, passport_error = validate_passport(nrc_number)
                if not passport_valid:
                    flash(f'Invalid ID: {nrc_error}', 'danger')
                    return render_template('register_land.html')

            # Validate TPIN if required
            tpin_val = (request.form.get('tpin_number') or '').strip()
            tpin_required_types = ['transfer','mortgage','change_ownership','title_issue']
            if registration_type in tpin_required_types:
                tpin_valid, tpin_error = validate_tpin(tpin_val)
                if not tpin_valid:
                    flash(f'Invalid TPIN: {tpin_error}', 'danger')
                    return render_template('register_land.html')
            
            # Validate phone
            phone_number = request.form.get('phone_number')
            if phone_number:
                phone_valid, phone_error = validate_phone(phone_number)
                if not phone_valid:
                    flash(f'Invalid phone: {phone_error}', 'danger')
                    return render_template('register_land.html')
            
            # Validate email
            email = request.form.get('email')
            if email:
                email_valid, email_error = validate_email(email)
                if not email_valid:
                    flash(f'Invalid email: {email_error}', 'danger')
                    return render_template('register_land.html')
            
            # Check for identity duplicates BEFORE creating application
            identity_dups = check_identity_duplicate(nrc_number, tpin_val)
            if identity_dups:
                dup_refs = ', '.join([app.reference_number for app in identity_dups[:3]])
                flash(f'Warning: Your NRC/TPIN matches existing application(s): {dup_refs}. ' +
                      'You may have already applied. Contact registry if this is an error.', 'warning')
                # Don't block, but warn user

            # Check for missing required documents
            missing = []
            for key in required_keys:
                if key == 'secured_amount':
                    if not request.form.get('secured_amount'):
                        missing.append('Secured Amount')
                    continue
                f = request.files.get(key)
                if not f or f.filename == '':
                    missing.append(key.replace('_', ' ').title())
            
            if missing:
                flash(f'Missing required: {", ".join(missing[:3])}{"..." if len(missing) > 3 else ""}', 'danger')
                return render_template('register_land.html')

            # Get and validate geometry
            geometry_json = request.form.get('land_geometry')
            if not geometry_json:
                flash('Please draw your land parcel on the map', 'danger')
                return render_template('register_land.html')

            # Parse geometry
            try:
                geom_dict = json.loads(geometry_json)
                geom = shape(geom_dict)
                geom_wkb = from_shape(geom, srid=4326)
            except Exception as e:
                current_app.logger.exception('Failed to parse geometry')
                flash('Invalid map geometry. Please redraw your parcel', 'danger')
                return render_template('register_land.html')

            # Create application
            application = LandApplication(
                reference_number=reference_number,
                applicant_name=request.form.get('applicant_name'),
                nrc_number=request.form.get('nrc_number'),
                tpin_number=request.form.get('tpin_number'),
                phone_number=request.form.get('phone_number'),
                email=request.form.get('email'),
                land_location=request.form.get('land_location'),
                land_size=float(request.form.get('land_size', 0)),
                land_use=request.form.get('land_use'),
                land_description=request.form.get('land_description'),
                declared_value=declared_value,
                status="pending",
                priority="medium",
                ai_conflict_score=0.0,
                ai_duplicate_score=0.0,
                ai_processed=False,
                processing_fee=payment_amount,
                payment_status="pending",
                user_id=current_user.id,
                registration_type=registration_type,
                coordinates=geom_wkb  # Add geometry here
            )
            db.session.add(application)
            db.session.flush()

            # Create parcel
            parcel = LandParcel(
                parcel_number=f"PN-{application.id}",
                owner_name=application.applicant_name,
                owner_nrc=application.nrc_number,
                owner_phone=application.phone_number,
                owner_email=application.email,
                size=application.land_size,
                location=application.land_location,
                land_use=application.land_use,
                land_description=application.land_description,
                status="registered",
                application_id=application.id,
                coordinates=geom_wkb  # Add geometry here too
            )
            db.session.add(parcel)

            # Document type labels
            label_map = {
                'nrc_copy': 'NRC Copy',
                'tpin_certificate': 'TPIN Certificate',
                'survey_map': 'Survey Map',
                'allocation_letter': 'Allocation Letter',
                'current_title_deed': 'Current Title Deed',
                'seller_id': 'Seller ID',
                'buyer_id': 'Buyer ID',
                'seller_tpin': 'Seller TPIN',
                'buyer_tpin': 'Buyer TPIN',
                'sale_agreement': 'Sale Agreement',
                'offer_letter': 'Offer Letter',
                'lease_agreement': 'Lease Agreement',
                'proof_rent': 'Proof of Rent',
                'mortgage_deed': 'Mortgage Deed',
                'lender_name_tpin': 'Lender Name & TPIN',
                'borrower_id': 'Borrower ID',
                'original_title_copy': 'Original Title Copy',
                'application_letter': 'Application Letter',
                'police_report': 'Police Report',
                'statutory_declaration': 'Statutory Declaration',
                'assignment_deed': 'Assignment Deed',
                'old_title_copy': 'Old Title Copy',
                'caveat_document': 'Caveat Document',
                'proof_of_interest': 'Proof of Interest'
            }

            # Save required files
            for key in required_keys:
                if key == 'secured_amount':
                    continue
                fileobj = request.files.get(key)
                if fileobj and fileobj.filename != "":
                    try:
                        saved = _save_upload(fileobj, current_user.id, application.id, key)
                    except ValueError as ve:
                        db.session.rollback()
                        flash(str(ve), 'danger')
                        return render_template('register_land.html')
                    
                    filepath = os.path.join(
                        current_app.config['UPLOAD_FOLDER'],
                        f"user_{current_user.id}",
                        f"app_{application.id}",
                        saved
                    )
                    
                    doc = Document(
                        application_id=application.id,
                        document_type=label_map.get(key, key.replace('_', ' ').title()),
                        filename=saved,
                        original_filename=fileobj.filename,
                        file_path=filepath,
                        file_size=os.path.getsize(filepath),
                        mime_type=fileobj.mimetype,
                        file_hash=hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
                    )
                    db.session.add(doc)

            # Save additional documents
            additional_files = request.files.getlist('additional_docs') or []
            for idx, fileobj in enumerate(additional_files):
                if fileobj and fileobj.filename != "":
                    saved = _save_upload(fileobj, current_user.id, application.id, f"additional_{idx}")
                    filepath = os.path.join(
                        current_app.config['UPLOAD_FOLDER'],
                        f"user_{current_user.id}",
                        f"app_{application.id}",
                        saved
                    )
                    doc = Document(
                        application_id=application.id,
                        document_type='Additional Document',
                        filename=saved,
                        original_filename=fileobj.filename,
                        file_path=filepath,
                        file_size=os.path.getsize(filepath),
                        mime_type=fileobj.mimetype,
                        file_hash=hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
                    )
                    db.session.add(doc)

            # Save secured amount if provided
            secured_amt_raw = request.form.get('secured_amount')
            if secured_amt_raw:
                try:
                    application.secured_amount = float(secured_amt_raw)
                except Exception:
                    application.secured_amount = None

            # Save annual rent if provided
            annual_rent_raw = request.form.get('annual_rent')
            if annual_rent_raw:
                try:
                    application.annual_rent = float(annual_rent_raw)
                except Exception:
                    application.annual_rent = None