document.addEventListener('DOMContentLoaded', function() {
    const registrationForm = document.getElementById('registrationForm');
    const formMessage = document.getElementById('form-message');

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

    if (registrationForm) {
        registrationForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            clearFormMessage();
            const errorMessages = document.querySelectorAll('.error-message');
            errorMessages.forEach(el => {
                el.textContent = '';
                el.style.display = 'none';
            });

            let isValid = true;

            const fullNames = document.getElementById('full-names').value.trim();
            const email = document.getElementById('email').value.trim();
            const phoneNumber = document.getElementById('phone-number').value.trim();
            const location = document.getElementById('location').value.trim();
            const dob = document.getElementById('dob').value.trim();
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;

            // --- Client-side validation (unchanged) ---
            if (fullNames === '') { displayError('full-names', 'Full Names are required.'); isValid = false; } else if (fullNames.length < 3) { displayError('full-names', 'Full Names must be at least 3 characters.'); isValid = false; }
            if (email === '') { displayError('email', 'Email Address is required.'); isValid = false; } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { displayError('email', 'Please enter a valid email address.'); isValid = false; }
            if (phoneNumber === '') { displayError('phone-number', 'Phone Number is required.'); isValid = false; } else if (!/^\+?[0-9\s()-]{7,20}$/.test(phoneNumber)) { displayError('phone-number', 'Please enter a valid phone number.'); isValid = false; }
            if (location === '') { displayError('location', 'Location is required.'); isValid = false; }
            if (dob === '') { displayError('dob', 'Date of Birth is required.'); isValid = false; } else { const selectedDate = new Date(dob); const today = new Date(); if (selectedDate > today) { displayError('dob', 'Date of Birth cannot be in the future.'); isValid = false; } const minAgeDate = new Date(); minAgeDate.setFullYear(today.getFullYear() - 18); if (selectedDate > minAgeDate) { displayError('dob', 'You must be at least 18 years old.'); isValid = false; } }
            if (password === '') { displayError('password', 'Password is required.'); isValid = false; } else if (password.length < 8) { displayError('password', 'Password must be at least 8 characters long.'); isValid = false; } else if (!/[A-Z]/.test(password)) { displayError('password', 'Password must contain at least one uppercase letter.'); isValid = false; } else if (!/[a-z]/.test(password)) { displayError('password', 'Password must contain at least one lowercase letter.'); isValid = false; } else if (!/[0-9]/.test(password)) { displayError('password', 'Password must contain at least one number.'); isValid = false; } else if (!/[^A-Za-z0-9]/.test(password)) { displayError('password', 'Password must contain at least one special character.'); isValid = false; }
            if (confirmPassword === '') { displayError('confirm-password', 'Confirm Password is required.'); isValid = false; } else if (password !== confirmPassword) { displayError('confirm-password', 'Passwords do not match.'); isValid = false; }
            // --- End client-side validation ---

            if (isValid) {
                try {
                    const response = await fetch('http://127.0.0.1:5000/api/register', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            fullNames,
                            email,
                            phoneNumber,
                            location,
                            dateOfBirth: dob,
                            password,
                            confirmPassword
                        }),
                    });

                    const data = await response.json();
                    console.log('Registration Response Status:', response.status);
                    console.log('Registration Response Data:', data);

                    if (response.ok) {
                        showFormMessage(data.msg || 'Registration successful!', 'success');
                        registrationForm.reset();
                        
                        // --- AUTOMATIC LOGIN AFTER REGISTRATION ---
                        if (data.access_token && data.role) {
                            localStorage.setItem('access_token', data.access_token);
                            localStorage.setItem('user_role', data.role);
                            // Redirect to dashboard based on role
                            if (data.role === 'admin') {
                                window.location.href = 'admin_dashboard.html';
                            } else {
                                window.location.href = 'user_dashboard.html';
                            }
                        } else {
                            // If token/role not returned, just show success and let user manually login
                            console.warn("Access token or role not received after registration. User needs to log in manually.");
                        }

                    } else {
                        showFormMessage(data.msg || 'Registration failed. Please try again.', 'error');
                    }
                } catch (error) {
                    console.error('Error during registration fetch:', error);
                    showFormMessage('Network error or server unavailable. Please try again later.', 'error');
                }
            } else {
                showFormMessage('Please correct the errors in the form.', 'error');
            }
        });
    }
});
