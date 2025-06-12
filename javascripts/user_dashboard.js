document.addEventListener('DOMContentLoaded', async function() {
    const welcomeMsg = document.getElementById('dashboard-welcome-msg');
    const userEmailSpan = document.getElementById('user-email');
    const userLocationSpan = document.getElementById('user-location');
    const userPhoneSpan = document.getElementById('user-phone');
    const logoutBtn = document.getElementById('logoutBtn');

    const accessToken = localStorage.getItem('access_token');
    const userRole = localStorage.getItem('user_role');

    // Redirect if not logged in or not a user
    if (!accessToken || userRole !== 'user') {
        alert('You are not authorized to view this page. Please log in as a user.');
        window.location.href = 'login.html'; // Redirect to login page
        return;
    }

    // Fetch user-specific data from the backend
    try {
        const response = await fetch('http://127.0.0.1:5000/api/user/dashboard', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`, // Send JWT token
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok) {
            welcomeMsg.textContent = data.msg;
            userEmailSpan.textContent = data.user_info.email;
            userLocationSpan.textContent = data.user_info.location;
            userPhoneSpan.textContent = data.user_info.phone_number;
            // You can populate more elements with data.data if needed
        } else {
            console.error('Failed to fetch user dashboard data:', data.msg);
            alert(`Error: ${data.msg || 'Failed to load dashboard data. Please log in again.'}`);
            // If token is invalid or expired, force logout
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_role');
            window.location.href = 'login.html';
        }
    } catch (error) {
        console.error('Network error fetching user dashboard:', error);
        alert('Network error. Could not connect to the server.');
        // Consider logging out or showing a persistent error message
    }

    // Logout functionality
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(event) {
            event.preventDefault();
            localStorage.removeItem('access_token'); // Clear token
            localStorage.removeItem('user_role'); // Clear role
            window.location.href = 'homepage.html'; // Redirect to homepage
        });
    }
});
