// register_land.js - COMPLETE FIXED VERSION
// Single responsibility: Handle land registration form ONLY

function debounce(fn, wait){
    let t; 
    return (...args)=>{
        clearTimeout(t); 
        t=setTimeout(()=>fn.apply(this,args), wait)
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('landForm');
    if (!form) return;

    console.log('✓ Register Land JS initialized');
    
    // HIDE ALL DOCUMENTS BY DEFAULT
    const requiredDocsContainer = document.getElementById('requiredDocs');
    if (requiredDocsContainer) {
        requiredDocsContainer.style.display = 'none';
    }

    // NRC AUTO-FORMATTING with slashes
    const nrcInput = document.getElementById('nrc_number');
    if (nrcInput) {
        nrcInput.addEventListener('input', function(e) {
            // Get only digits
            let value = e.target.value.replace(/\D/g, '');
            let formatted = '';
            
            // Format as XXXXXX/XX/X
            if (value.length > 0) {
                formatted = value.substring(0, 6); // First 6 digits
                if (value.length > 6) {
                    formatted += '/' + value.substring(6, 8); // Slash + 2 digits
                }
                if (value.length > 8) {
                    formatted += '/' + value.substring(8, 9); // Slash + 1 digit
                }
            }
            
            // Set the formatted value
            e.target.value = formatted;
        });
        
        // Prevent typing beyond 10 characters (including slashes)
        nrcInput.addEventListener('keydown', function(e) {
            const allowedKeys = ['Backspace', 'Delete', 'Tab', 'ArrowLeft', 'ArrowRight', 'Home', 'End'];
            if (e.target.value.length >= 10 && !allowedKeys.includes(e.key)) {
                e.preventDefault();
            }
        });
        
        // Validate on blur
        nrcInput.addEventListener('blur', function(e) {
            const value = e.target.value;
            const validPattern = /^\d{6}\/\d{2}\/\d$/;
            
            if (value && !validPattern.test(value)) {
                e.target.classList.add('is-invalid');
            } else {
                e.target.classList.remove('is-invalid');
            }
        });
    }

    // File input handlers
    document.querySelectorAll('.custom-file-label').forEach(label => {
        const input = document.getElementById(label.getAttribute('for'));
        const span = label.querySelector('.file-name-preview');
        if (!input) return;
        
        input.addEventListener('change', function(){
            const icon = label.querySelector('i');
            if (this.files && this.files.length){
                if (this.multiple) {
                    span.textContent = `${this.files.length} file(s) selected`;
                } else {
                    span.textContent = this.files[0].name;
                }
                span.style.color = '#198754';
                if (icon) {
                    icon.className = 'fas fa-check-circle';
                    icon.style.color = '#198754';
                }
            } else { 
                span.textContent = span.getAttribute('data-default') || 'Choose file'; 
                span.style.color='';
                if (icon) {
                    icon.className = 'fas fa-cloud-upload-alt';
                    icon.style.color = '';
                }
            }
        });
        
        label.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            input.click();
        });
    });

    // Payment tile selection
    document.querySelectorAll('.pay-tile').forEach(tile => {
        tile.addEventListener('click', () => selectPayment(tile));
    });

    function selectPayment(tile){
        document.querySelectorAll('.pay-tile').forEach(t=>t.classList.remove('selected'));
        tile.classList.add('selected');
        const val = tile.getAttribute('data-value');
        const radio = document.querySelector(`input[name=payment_method][value="${val}"]`);
        if (radio) radio.checked = true;
        renderPaymentFields(val);
    }

    function renderPaymentFields(method){
        const container = document.getElementById('payment-extra-fields');
        if (!container) return;
        container.innerHTML = '';
        if (!method) return;
        
        if (['mtn','airtel','zamtel'].includes(method)){
            let placeholder = '+260971234567';
            let example = '097XXXXXXX';
            if (method === 'mtn') {
                placeholder = '+260961234567';
                example = '096XXXXXXX';
            } else if (method === 'airtel') {
                placeholder = '+260971234567';
                example = '097XXXXXXX';
            } else if (method === 'zamtel') {
                placeholder = '+260951234567';
                example = '095XXXXXXX';
            }
            container.innerHTML = `
                <div class="row g-3">
                    <div class="col-md-6">
                        <label for="mobile_phone" class="form-label">Mobile wallet phone number</label>
                        <input id="mobile_phone" name="mobile_phone" type="tel" class="form-control" placeholder="${placeholder}">
                        <div class="form-text">Enter your ${method.toUpperCase()} number (e.g., ${example})</div>
                    </div>
                    <div class="col-md-6">
                        <label for="mobile_reference" class="form-label">Payment reference (optional)</label>
                        <input id="mobile_reference" name="mobile_reference" class="form-control" placeholder="Optional reference">
                    </div>
                </div>
            `;
        } else if (method === 'visa'){
            const currentYear = new Date().getFullYear();
            const months = ['01','02','03','04','05','06','07','08','09','10','11','12'];
            const years = [];
            for (let i = 0; i < 15; i++) years.push(currentYear + i);
            
            container.innerHTML = `
                <div class="row g-3">
                    <div class="col-md-6">
                        <label for="card_number" class="form-label">Card number</label>
                        <input id="card_number" name="card_number" class="form-control" placeholder="1234 5678 9012 3456" maxlength="19" inputmode="numeric">
                    </div>
                    <div class="col-md-3">
                        <label for="card_exp_month" class="form-label">Month</label>
                        <select id="card_exp_month" name="card_exp_month" class="form-select">
                            <option value="">MM</option>
                            ${months.map(m => `<option value="${m}">${m}</option>`).join('')}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label for="card_exp_year" class="form-label">Year</label>
                        <select id="card_exp_year" name="card_exp_year" class="form-select">
                            <option value="">YYYY</option>
                            ${years.map(y => `<option value="${y}">${y}</option>`).join('')}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label for="card_cvc" class="form-label">CVC</label>
                        <input id="card_cvc" name="card_cvc" class="form-control" placeholder="123" maxlength="3" inputmode="numeric">
                    </div>
                    <div class="col-md-6">
                        <label for="card_name" class="form-label">Name on card</label>
                        <input id="card_name" name="card_name" class="form-control" placeholder="Jane Doe">
                    </div>
                </div>
            `;
            
            const cardNumEl = document.getElementById('card_number');
            if (cardNumEl) {
                cardNumEl.addEventListener('input', (e) => {
                    let value = e.target.value.replace(/\D/g, '');
                    let formatted = value.match(/.{1,4}/g)?.join(' ') || value;
                    e.target.value = formatted.substring(0, 19);
                });
            }
        } else if (method === 'bank'){
            container.innerHTML = `
                <div class="row g-3">
                    <div class="col-12">
                        <label for="bank_receipt" class="form-label">Upload bank deposit receipt</label>
                        <input id="bank_receipt" name="bank_receipt" type="file" accept=".pdf,.jpg,.png" class="form-control">
                    </div>
                </div>
            `;
        }
    }

    // Registration types with requirements
    const registrationTypes = {
        transfer: {
            fee: 0,
            required: ['seller_id','buyer_id','seller_tpin','buyer_tpin','sale_agreement','current_title_deed'],
            needsDeclaredValue: true,
            category: 'I',
            regPercent: 0.02,
            description: 'Transfer of land ownership'
        },
        change_ownership: { 
            fee: 0, 
            required: ['assignment_deed','old_title_copy','seller_tpin','buyer_tpin','nrc_copy'], 
            needsDeclaredValue: true, 
            category: 'I',
            regPercent: 0.02,
            description: 'Change of ownership'
        },
        mortgage: { 
            fee: 0, 
            required: ['mortgage_deed','lender_name_tpin','borrower_id','secured_amount'], 
            needsDeclaredValue: true, 
            category: 'II',
            regPercent: 0.02,
            description: 'Mortgage registration'
        },
        lease: { 
            fee: 0,
            required: ['offer_letter','lease_agreement','survey_map','proof_rent','nrc_copy','tpin_certificate'], 
            needsDeclaredValue: false,
            needsAnnualRent: true,
            category: 'III',
            regPercent: 0.02,
            description: 'Lease registration'
        },
        title_issue: { 
            fee: 278,
            required: ['offer_letter','survey_map','nrc_copy','tpin_certificate'], 
            needsDeclaredValue: false,
            description: 'New title issue'
        },
        subdivision: { 
            fee: 800, 
            required: ['original_title_copy','survey_map','nrc_copy','application_letter'], 
            needsDeclaredValue: false,
            description: 'Property subdivision'
        },
        replacement: { 
            fee: 500, 
            required: ['police_report','statutory_declaration','nrc_copy'], 
            needsDeclaredValue: false,
            description: 'Lost/damaged title replacement'
        },
        caveat: { 
            fee: 400, 
            required: ['caveat_document','nrc_copy','proof_of_interest'], 
            needsDeclaredValue: false,
            description: 'Caveat registration'
        }
    };

    function formatZMW(n){ 
        return 'ZMW ' + (isNaN(n) ? '0.00' : Number(n).toFixed(2)); 
    }

    function updateFeeSummary(){
        const typeEl = document.getElementById('registration_type');
        if (!typeEl) return;
        const type = typeEl.value;
        const cfg = registrationTypes[type] || {};
        const declared = parseFloat((document.getElementById('declared_value').value || '').replace(/,/g,'')) || 0;
        let reg = 0;
        
        if (cfg.category === 'I' && cfg.needsDeclaredValue) {
            reg = declared * (cfg.regPercent || 0.02);
        } else if (cfg.category === 'II') {
            const securedInput = document.querySelector('input[name="secured_amount"]');
            const secured = parseFloat(securedInput ? securedInput.value : 0) || 0;
            reg = secured * (cfg.regPercent || 0.02);
        } else if (cfg.category === 'III' && cfg.needsAnnualRent) {
            const rentInput = document.querySelector('input[name="annual_rent"]');
            const annualRent = parseFloat(rentInput ? rentInput.value : 0) || 0;
            reg = annualRent * (cfg.regPercent || 0.02);
        } else {
            reg = cfg.fee || 0;
        }
        
        const total = reg;
        const sumDeclared = document.getElementById('sumDeclared'); 
        if (sumDeclared) sumDeclared.textContent = formatZMW(declared);
        const sumReg = document.getElementById('sumReg'); 
        if (sumReg) sumReg.textContent = formatZMW(reg);
        const sumTotal = document.getElementById('sumTotal'); 
        if (sumTotal) sumTotal.textContent = formatZMW(total);
        const regFeeEl = document.getElementById('registration_fee'); 
        if (regFeeEl) regFeeEl.value = Number(reg || 0).toFixed(2);
        const payAmtEl = document.getElementById('payment_amount'); 
        if (payAmtEl) payAmtEl.value = Number(total || 0).toFixed(2);
        
        const declaredValueRow = document.getElementById('declaredValueRow');
        if (declaredValueRow) {
            declaredValueRow.style.display = cfg.needsDeclaredValue ? '' : 'none';
        }
        
        const feeDescEl = document.getElementById('feeDescription');
        if (feeDescEl && cfg.description) {
            let desc = cfg.description;
            if (cfg.category) {
                desc = `Category ${cfg.category}: ${desc}`;
            }
            feeDescEl.textContent = desc;
        }
    }

    function updateRequiredDocs(selectedType){
        const cfg = registrationTypes[selectedType] || {fee:'', required:[]};
        const requiredDocsContainer = document.getElementById('requiredDocs');
        
        // HIDE if no type selected
        if (!selectedType) { 
            if (requiredDocsContainer) requiredDocsContainer.style.display = 'none'; 
            return; 
        }
        
        // SHOW when type is selected
        if (requiredDocsContainer) requiredDocsContainer.style.display = '';
        updateFeeSummary();
        
        // Show/hide each document field based on requirements
        document.querySelectorAll('#requiredDocs .doc-field').forEach(div=>{
            const key = div.getAttribute('data-doc');
            const input = div.querySelector('input[type=file], input[type=number]');
            const label = div.querySelector('.form-label');
            if (!key) return;
            
            // Handle annual_rent field
            if (key === 'annual_rent') {
                if (cfg.needsAnnualRent) {
                    div.style.display = '';
                    if (input) { 
                        input.required = true; 
                        input.setAttribute('aria-required','true'); 
                    }
                    if (label && !label.querySelector('.required-star')) {
                        label.innerHTML += ' <span class="required-star">*</span>';
                    }
                } else {
                    div.style.display = 'none';
                    if (input) { 
                        input.required = false; 
                        input.removeAttribute('aria-required'); 
                    }
                }
                return;
            }
            
            // Show if required OR if it's additional_docs
            if (cfg.required.includes(key) || key==='additional_docs'){
                div.style.display = '';
                if (cfg.required.includes(key) && input) { 
                    input.required = true; 
                    input.setAttribute('aria-required','true'); 
                } else if (input) { 
                    input.required = false; 
                    input.removeAttribute('aria-required'); 
                }
                if (label && cfg.required.includes(key) && !label.querySelector('.required-star')) {
                    label.innerHTML += ' <span class="required-star">*</span>';
                }
            } else {
                // HIDE if not required
                div.style.display = 'none';
                if (input) { 
                    input.required = false; 
                    input.removeAttribute('aria-required'); 
                }
                // Remove star if exists
                if (label && label.querySelector('.required-star')) {
                    const star = label.querySelector('.required-star');
                    if (star) star.remove();
                }
            }
        });
    }

    const preSelected = document.querySelector('input[name=payment_method]:checked');
    if (preSelected) renderPaymentFields(preSelected.value);

    const regEl = document.getElementById('registration_type');
    if (regEl) {
        regEl.addEventListener('change', (e)=>{ 
            updateRequiredDocs(e.target.value); 
            updateFeeSummary(); 
        });
        // Trigger on load if value already set
        if (regEl.value) updateRequiredDocs(regEl.value);
    }
    
    const declEl = document.getElementById('declared_value');
    if (declEl) declEl.addEventListener('input', debounce(updateFeeSummary, 300));
    
    const securedEl = document.getElementById('secured_amount');
    if (securedEl) securedEl.addEventListener('input', debounce(updateFeeSummary, 300));
    
    const annualRentEl = document.getElementById('annual_rent');
    if (annualRentEl) annualRentEl.addEventListener('input', debounce(updateFeeSummary, 300));

    // MAP INITIALIZATION - ENHANCED VERSION
    if (document.getElementById('map')){
        // Initialize map with better controls
        var map = L.map('map', { 
            center: [-12.9640, 28.6367], 
            zoom: 13,
            zoomControl: true
        });
        
        // Add multiple tile layers
        var streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap',
            maxZoom: 19
        });
        
        var satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: '© Esri',
            maxZoom: 19
        });
        
        var hybridLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: '© Esri'
        });
        var labelLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap',
            opacity: 0.4
        });
        var hybridGroup = L.layerGroup([hybridLayer, labelLayer]);
        
        // Add street layer by default
        streetLayer.addTo(map);
        
        // Layer control for switching views
        var baseMaps = {
            "<i class='fas fa-map'></i> Street Map": streetLayer,
            "<i class='fas fa-satellite'></i> Satellite": satelliteLayer,
            "<i class='fas fa-layer-group'></i> Hybrid": hybridGroup
        };
        
        L.control.layers(baseMaps, null, {
            position: 'topright',
            collapsed: false
        }).addTo(map);
        
        var drawnItems = new L.FeatureGroup(); 
        map.addLayer(drawnItems);
        
        var drawControl = new L.Control.Draw({ 
            draw:{
                polygon:{allowIntersection:false,showArea:true, metric: true},
                rectangle:true,
                marker:true,
                polyline:false,
                circle:false
            }, 
            edit:{featureGroup:drawnItems} 
        });
        map.addControl(drawControl);
        
        function setGeometryAndArea(layer){
            var geo = layer.toGeoJSON().geometry; 
            const geoEl = document.getElementById('land_geometry'); 
            if (geoEl) geoEl.value = JSON.stringify(geo);
            
            if (geo.type === 'Polygon' || geo.type === 'MultiPolygon'){ 
                var area_m2 = turf.area(geo); 
                const sizeEl = document.getElementById('land_size'); 
                if (sizeEl) sizeEl.value = (area_m2/10000).toFixed(4); 
            } else { 
                const sizeEl = document.getElementById('land_size'); 
                if (sizeEl) sizeEl.value = ''; 
            }
        }
        
        map.on(L.Draw.Event.CREATED, function(e){ 
            drawnItems.clearLayers(); 
            drawnItems.addLayer(e.layer); 
            setGeometryAndArea(e.layer); 
        });
        
        map.on('draw:edited', function(e){ 
            e.layers.eachLayer(l=>setGeometryAndArea(l)); 
        });
        
        map.on('click', function(e){ 
            if (drawnItems.getLayers().length===0){ 
                var m=L.marker(e.latlng,{draggable:true}).addTo(drawnItems); 
                setGeometryAndArea(m); 
                m.on('dragend', ()=>setGeometryAndArea(m)); 
            } 
        });
        
        const btnLocate = document.getElementById('btnLocate');
        if (btnLocate){ 
            btnLocate.addEventListener('click', ()=>{ 
                if (!navigator.geolocation){ 
                    alert('Geolocation not available'); 
                    return;
                } 
                btnLocate.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Locating...';
                btnLocate.disabled = true;
                navigator.geolocation.getCurrentPosition(p=>{ 
                    var latlng=[p.coords.latitude,p.coords.longitude]; 
                    map.setView(latlng,17); 
                    drawnItems.clearLayers(); 
                    var m=L.marker(latlng,{draggable:true}).addTo(drawnItems); 
                    setGeometryAndArea(m); 
                    m.on('dragend', ()=>setGeometryAndArea(m)); 
                    btnLocate.innerHTML = '<i class="fas fa-crosshairs me-1"></i>Use My Location';
                    btnLocate.disabled = false;
                }, err=>{
                    alert('Could not get location: '+err.message);
                    btnLocate.innerHTML = '<i class="fas fa-crosshairs me-1"></i>Use My Location';
                    btnLocate.disabled = false;
                }, {enableHighAccuracy:true}); 
            }); 
        }
        
        // ENHANCED LOCATION SEARCH
        const landLocationInput = document.getElementById('land_location');
        if (landLocationInput) {
            let searchTimeout;
            let searchMarker;
            
            landLocationInput.addEventListener('input', function(e) {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                
                if (query.length < 3) return;
                
                searchTimeout = setTimeout(async () => {
                    try {
                        // Use Nominatim for geocoding
                        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query + ', Ndola, Zambia')}&limit=1`);
                        const data = await response.json();
                        
                        if (data && data.length > 0) {
                            const result = data[0];
                            const lat = parseFloat(result.lat);
                            const lon = parseFloat(result.lon);
                            
                            // Move map to location
                            map.setView([lat, lon], 16);
                            
                            // Add temporary marker
                            if (searchMarker) {
                                map.removeLayer(searchMarker);
                            }
                            searchMarker = L.marker([lat, lon], {
                                icon: L.icon({
                                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                                    iconSize: [25, 41],
                                    iconAnchor: [12, 41],
                                    popupAnchor: [1, -34],
                                    shadowSize: [41, 41]
                                })
                            }).addTo(map);
                            searchMarker.bindPopup(`<b>${result.display_name}</b><br><small>Click map to mark your parcel</small>`).openPopup();
                            
                            // Auto-remove marker after 5 seconds
                            setTimeout(() => {
                                if (searchMarker) {
                                    map.removeLayer(searchMarker);
                                    searchMarker = null;
                                }
                            }, 5000);
                        }
                    } catch (err) {
                        console.log('Geocoding error:', err);
                    }
                }, 800);
            });
            
            // Add search hint
            const locationGroup = landLocationInput.closest('.mb-3');
            if (locationGroup && !locationGroup.querySelector('.search-hint')) {
                const hint = document.createElement('small');
                hint.className = 'form-text search-hint';
                hint.innerHTML = '<i class="fas fa-lightbulb me-1"></i>Type a location to automatically zoom the map';
                landLocationInput.parentNode.appendChild(hint);
            }
        }
        
        const btnResetMap = document.getElementById('btnResetMap');
        if (btnResetMap){ 
            btnResetMap.addEventListener('click', ()=>{ 
                drawnItems.clearLayers(); 
                const geoEl = document.getElementById('land_geometry'); 
                if (geoEl) geoEl.value=''; 
                const sizeEl = document.getElementById('land_size'); 
                if (sizeEl) sizeEl.value=''; 
            }); 
        }
    }

    // FORM SUBMIT - Enhanced with error scrolling
    form.addEventListener('submit', async (e)=>{
        e.preventDefault();
        e.stopPropagation();
        
        console.log('→ Form submit triggered');
        
        // Basic HTML5 validation with error scrolling
        if (!form.checkValidity()) { 
            form.classList.add('was-validated');
            
            // Find first invalid field and scroll to it
            const firstInvalid = form.querySelector(':invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                setTimeout(() => firstInvalid.focus(), 500);
                
                // Show error message
                const errorMsg = firstInvalid.validationMessage;
                const label = form.querySelector(`label[for="${firstInvalid.id}"]`);
                if (label) {
                    alert(`Error in ${label.textContent.replace('*', '').trim()}: ${errorMsg}`);
                }
            }
            
            console.log('✗ HTML5 validation failed');
            return; 
        }

        // Check geometry with scroll
        if (!document.getElementById('land_geometry').value){ 
            const mapEl = document.getElementById('map');
            if (mapEl) {
                mapEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            alert('Please draw your parcel on the map');
            console.log('✗ No geometry');
            return; 
        }

        // Check NRC format with scroll
        const nrcVal = (document.getElementById('nrc_number').value || '').trim();
        if (!/^\d{6}\/\d{2}\/\d$/.test(nrcVal)) {
            const nrcEl = document.getElementById('nrc_number');
            if (nrcEl) {
                nrcEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                setTimeout(() => nrcEl.focus(), 500);
            }
            alert('NRC must be in format 123456/78/9');
            console.log('✗ Invalid NRC');
            return;
        }

        // Disable submit button
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
        }
        
        console.log('✓ Validation passed, submitting...');
        form.submit();
    });

    console.log('✓ Register Land JS fully loaded');
});
