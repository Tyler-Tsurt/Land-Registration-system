document.addEventListener('DOMContentLoaded', function() {
    const landApplicationForm = document.getElementById('landApplicationForm');
    const formMessage = document.getElementById('form-message');
    const logoutBtn = document.getElementById('logoutBtn');

    // Check if user is logged in, otherwise redirect to login page
    const accessToken = localStorage.getItem('access_token');
    const userRole = localStorage.getItem('user_role');

    if (!accessToken) {
        alert('You need to be logged in to register land.');
        window.location.href = 'login.html';
        return;
    }

    // Helper functions for displaying messages (reused from register/login.js)
    function displayError(elementId, message) {
        const errorElement = document.getElementById(elementId + '-error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }

    function clearError(elementId) {
        const errorElement = document.getElementById(elementId + '-error');
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.style.display = 'none';
        }
    }

    function showFormMessage(message, type) {
        formMessage.textContent = message;
        formMessage.className = 'form-message ' + type;
        formMessage.style.display = 'block';
    }

    function clearFormMessage() {
        formMessage.textContent = '';
        formMessage.className = 'form-message';
        formMessage.style.display = 'none';
    }

    // Logout functionality (reused from dashboards)
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(event) {
            event.preventDefault();
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_role');
            window.location.href = 'homepage.html';
        });
    }

    if (landApplicationForm) {
        landApplicationForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            clearFormMessage();
            document.querySelectorAll('.error-message').forEach(el => {
                el.textContent = '';
                el.style.display = 'none';
            });

            let isValid = true;

            const landLocation = document.getElementById('land-location').value.trim();
            const nationalIdFile = document.getElementById('national-id').files;
            const proofOfOwnershipFile = document.getElementById('proof-of-ownership').files;
            const sitePlanFile = document.getElementById('site-plan').files;

            // Client-side validation for mandatory fields
            if (landLocation === '') {
                displayError('land-location', 'Land location is required.');
                isValid = false;
            }
            if (nationalIdFile.length === 0) {
                displayError('national-id', 'National ID / Passport is mandatory.');
                isValid = false;
            }
            if (proofOfOwnershipFile.length === 0) {
                displayError('proof-of-ownership', 'Proof of Previous Ownership is mandatory.');
                isValid = false;
            }
            if (sitePlanFile.length === 0) {
                displayError('site-plan', 'Site Plan is mandatory.');
                isValid = false;
            }

            if (!isValid) {
                showFormMessage('Please correct the errors in the form.', 'error');
                return; // Stop if client-side validation fails
            }

            // Prepare FormData for file uploads
            const formData = new FormData();
            formData.append('landLocation', landLocation);

            // Append pictures (optional, can be multiple)
            const landPictures = document.getElementById('land-pictures').files;
            for (let i = 0; i < landPictures.length; i++) {
                formData.append('pictures', landPictures[i]);
            }

            // Append required documents (can be multiple, but we're treating individual mandatory fields)
            // Note: The backend expects all file inputs with name="documents" to be collected under one 'documents' key
            // So we'll append all document files under the same 'documents' key.
            const documentFiles = document.querySelectorAll('input[name="documents"]');
            documentFiles.forEach(input => {
                for (let i = 0; i < input.files.length; i++) {
                    formData.append('documents', input.files[i]);
                }
            });

            try {
                const response = await fetch('http://127.0.0.1:5000/api/apply_land', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`, // Send JWT token
                        // 'Content-Type': 'multipart/form-data' is NOT set manually for FormData
                    },
                    body: formData, // FormData automatically sets Content-Type header
                });

                const data = await response.json();
                console.log('Land Application Response Status:', response.status);
                console.log('Land Application Response Data:', data);

                if (response.ok) {
                    showFormMessage(data.msg || 'Land application submitted successfully!', 'success');
                    landApplicationForm.reset(); // Clear the form
                } else {
                    showFormMessage(data.msg || 'Land application failed. Please try again.', 'error');
                }
            } catch (error) {
                console.error('Error during land application fetch:', error);
                showFormMessage('Network error or server unavailable. Please try again later.', 'error');
            }
        });
    }
});
