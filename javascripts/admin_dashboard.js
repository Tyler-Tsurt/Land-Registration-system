document.addEventListener('DOMContentLoaded', async function() {
    const welcomeMsg = document.getElementById('dashboard-welcome-msg');
    const totalUsersSpan = document.getElementById('total-users');
    const recentUsersSpan = document.getElementById('recent-users');
    const adminDataSpan = document.getElementById('admin-data');
    const logoutBtn = document.getElementById('logoutBtn');

    const accessToken = localStorage.getItem('access_token');
    const userRole = localStorage.getItem('user_role');

    // Redirect if not logged in or not an admin
    if (!accessToken || userRole !== 'admin') {
        alert('You are not authorized to view this page. Please log in as an administrator.');
        window.location.href = 'login.html'; // Redirect to login page
        return;
    }

    // Fetch admin-specific data from the backend
    try {
        const response = await fetch('http://127.0.0.1:5000/api/admin/dashboard', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${accessToken}`, // Send JWT token
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok) {
            welcomeMsg.textContent = data.msg;
            totalUsersSpan.textContent = data.all_users_count;
            recentUsersSpan.textContent = data.users_list_preview.join(', ') || 'None';
            adminDataSpan.textContent = data.admin_specific_data;
        } else {
            console.error('Failed to fetch admin dashboard data:', data.msg);
            alert(`Error: ${data.msg || 'Failed to load dashboard data. Please log in again.'}`);
            // If token is invalid or expired, force logout
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_role');
            window.location.href = 'login.html';
        }
    } catch (error) {
        console.error('Network error fetching admin dashboard:', error);
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
