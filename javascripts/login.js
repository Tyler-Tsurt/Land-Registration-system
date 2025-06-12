document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
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

    if (loginForm) {
        loginForm.addEventListener('submit', async function(event) {
            event.preventDefault();

            clearFormMessage();
            const errorMessages = document.querySelectorAll('.error-message');
            errorMessages.forEach(el => {
                el.textContent = '';
                el.style.display = 'none';
            });

            let isValid = true;

            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;

            // --- Client-side validation (unchanged) ---
            if (email === '') { displayError('email', 'Email Address is required.'); isValid = false; } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { displayError('email', 'Please enter a valid email address.'); isValid = false; }
            if (password === '') { displayError('password', 'Password is required.'); isValid = false; }
            // --- End client-side validation ---

            if (isValid) {
                try {
                    const response = await fetch('http://127.0.0.1:5000/api/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ email, password }),
                    });

                    const data = await response.json();
                    console.log('Login Response Status:', response.status); // DEBUG
                    console.log('Login Response Data:', data); // DEBUG

                    if (response.ok) {
                        localStorage.setItem('access_token', data.access_token);
                        localStorage.setItem('user_role', data.role);

                        showFormMessage('Login successful! Redirecting...', 'success');

                        if (data.role === 'admin') {
                            window.location.href = 'admin_dashboard.html';
                        } else {
                            window.location.href = 'user_dashboard.html';
                        }
                    } else {
                        // This block will now correctly execute for non-2xx responses (like 401)
                        showFormMessage(data.msg || 'Login failed. Please check your credentials.', 'error');
                    }
                } catch (error) {
                    console.error('Error during login fetch:', error); // DEBUG: Network errors
                    showFormMessage('Network error or server unavailable. Please try again later.', 'error');
                }
            } else {
                showFormMessage('Please correct the errors in the form.', 'error');
            }
        });
    }
});
