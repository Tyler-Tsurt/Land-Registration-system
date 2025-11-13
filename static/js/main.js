// Ndola Land Registry System - Main JavaScript
// Contains shared utilities and general functionality
// NOTE: Page-specific functionality (like register_land) is in separate files

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Navigation active state
    updateNavigationActiveState();
    
    // Auto-hide alerts after 5 seconds
    autoHideAlerts();
    
    // Initialize dashboard features if on admin page
    if (document.querySelector('.dashboard-card')) {
        initializeDashboard();
    }

    // Only initialize basic form validation for non-registration forms
    // Registration form is handled by register_land.js
    if (!document.getElementById('landForm')) {
        initializeBasicFormValidation();
    }
});

// Basic Form Validation - ONLY for non-registration forms
function initializeBasicFormValidation() {
    const forms = document.querySelectorAll('form[novalidate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            } else {
                // Show loading state
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.hasAttribute('data-no-loading')) {
                    const originalText = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
                    submitBtn.disabled = true;
                    
                    // Re-enable after 3 seconds if form is still on page
                    setTimeout(() => {
                        if (document.body.contains(submitBtn)) {
                            submitBtn.innerHTML = originalText;
                            submitBtn.disabled = false;
                        }
                    }, 3000);
                }
            }
            form.classList.add('was-validated');
        });
    });
}

// Navigation Active State
function updateNavigationActiveState() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// Auto-hide Alerts
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 500);
            }
        }, 5000);
    });
}

// Dashboard Functionality
function initializeDashboard() {
    // Animate dashboard statistics on load
    animateCounters();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize sorting
    initializeTableSorting();
    
    // Initialize filters
    initializeFilters();
}

// Animate Counter Numbers
function animateCounters() {
    const counters = document.querySelectorAll('.dashboard-stat-number');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent.replace(/,/g, ''));
        if (isNaN(target)) return;
        
        const duration = 2000; // 2 seconds
        const steps = 60;
        const increment = target / steps;
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.textContent = target.toLocaleString();
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current).toLocaleString();
            }
        }, duration / steps);
    });
}

// Search Functionality
function initializeSearch() {
    const searchInput = document.querySelector('input[placeholder*="Search"]');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('tbody tr');
            
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

// Table Sorting
function initializeTableSorting() {
    const tableHeaders = document.querySelectorAll('th[data-sort]');
    
    tableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.innerHTML += ' <i class="fas fa-sort text-muted"></i>';
        
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const column = this.cellIndex;
            const isAscending = this.classList.contains('sort-asc');
            
            // Remove sort classes from all headers
            tableHeaders.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
            
            // Sort rows
            rows.sort((a, b) => {
                const aText = a.cells[column].textContent.trim();
                const bText = b.cells[column].textContent.trim();
                
                if (isAscending) {
                    return bText.localeCompare(aText);
                } else {
                    return aText.localeCompare(bText);
                }
            });
            
            // Add sort class to current header
            this.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
            
            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// Filter Functionality
function initializeFilters() {
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const filterValue = this.value;
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                if (filterValue === '' || row.textContent.includes(filterValue)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
}

// Utility Functions
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 400px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Application-specific functions
function approveApplication(referenceNumber) {
    confirmAction(`Are you sure you want to approve application ${referenceNumber}?`, () => {
        showNotification(`Application ${referenceNumber} approved successfully!`, 'success');
    });
}

function rejectApplication(referenceNumber) {
    const reason = prompt('Please provide a reason for rejection:');
    if (reason) {
        confirmAction(`Are you sure you want to reject application ${referenceNumber}?`, () => {
            showNotification(`Application ${referenceNumber} rejected.`, 'warning');
        });
    }
}

function viewApplicationDetails(referenceNumber) {
    const modal = new bootstrap.Modal(document.getElementById('reviewApplicationModal'));
    modal.show();
}

// AI Conflict Detection Simulation
function checkForConflicts() {
    showNotification('Running AI conflict detection...', 'info');
    
    setTimeout(() => {
        const conflicts = Math.floor(Math.random() * 5);
        if (conflicts > 0) {
            showNotification(`${conflicts} potential conflicts detected!`, 'warning');
        } else {
            showNotification('No conflicts detected.', 'success');
        }
    }, 2000);
}

// Export functions for global access
window.ndolaLandRegistry = {
    approveApplication,
    rejectApplication,
    viewApplicationDetails,
    checkForConflicts,
    showNotification,
    // Fetch persisted conflicts for an application (calls /api/get_conflicts)
    fetchConflictsForApplication: async function(applicationId){
        if (!applicationId) return [];
        try{
            const res = await fetch(`/api/get_conflicts?application_id=${encodeURIComponent(applicationId)}`);
            if (!res.ok) return [];
            return await res.json();
        }catch(e){ console.error('Failed to fetch conflicts', e); return []; }
    },
    // Render conflicts on a Leaflet map. Accepts either a Leaflet map or an element id.
    renderConflictsOnMap: function(mapInstance, conflicts){
        if (!window.L) return;
        try{
            const map = mapInstance && mapInstance._leaflet_id ? mapInstance : (typeof mapInstance === 'string' ? window[mapInstance] : null);
            if (!map) {
                console.warn('No map provided to render conflicts');
                return;
            }

            // keep a dedicated layer group for conflicts
            if (!this._conflictLayer) this._conflictLayer = L.layerGroup().addTo(map);
            this._conflictLayer.clearLayers();

            conflicts = conflicts || [];
            // Only render conflicts that meet a minimal confidence/overlap threshold
            const MIN_CONF_THRESHOLD = 0.02; // 2% overlap/confidence minimum
            conflicts.filter(c => {
                const score = (c.confidence_score || c.overlap_percentage || 0);
                return (typeof score === 'number') ? (score >= MIN_CONF_THRESHOLD) : true;
            }).forEach(c => {
                const parcel = c.parcel || {};
                if (parcel && parcel.geojson){
                    try{
                        const gj = parcel.geojson;
                        const layer = L.geoJSON(gj, {
                            style: function(){
                                return { color: '#d9534f', weight: 2, fillOpacity: 0.12 };
                            }
                        });
                        layer.bindPopup(`<strong>${c.title || parcel.parcel_number || ''}</strong><br/>Confidence: ${(c.confidence_score||c.overlap_percentage||0).toFixed? (c.confidence_score||0).toFixed(2) : (c.confidence_score||c.overlap_percentage||0)}`);
                        layer.addTo(this._conflictLayer);
                    }catch(err){ console.error('Failed to render parcel geojson', err); }
                } else if (c.geojson){
                    // older format where top-level item contains geojson
                    try{ L.geoJSON(c.geojson, { style: { color:'#d9534f', weight:2, fillOpacity:0.15 } }).addTo(this._conflictLayer); }catch(e){}
                } else if (c.lat && c.lng){
                    const m = L.marker([c.lat, c.lng]).addTo(this._conflictLayer);
                    m.bindPopup(c.title || 'Potential conflict');
                }
            });

            // Fit map to conflicts if any
            try{
                const layers = this._conflictLayer.getLayers();
                if (layers.length > 0){
                    const g = L.featureGroup(layers);
                    map.fitBounds(g.getBounds().pad(0.2));
                }
            }catch(e){/* ignore */}
        }catch(e){ console.error('renderConflictsOnMap error', e); }
    }
};
