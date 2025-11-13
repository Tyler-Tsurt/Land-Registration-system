document.addEventListener('DOMContentLoaded', function() {
    const authNav = document.getElementById('auth-nav');

    fetch('/api/check-auth', { method: 'GET', credentials: 'same-origin' })
        .then(response => response.json())
        .then(data => {
            authNav.innerHTML = ''; // Clear placeholder

            if (data.authenticated) {
                //  Always show logout
                authNav.innerHTML += `
                    <a class="nav-link" href="/logout">
                        <i class="fas fa-sign-out-alt me-1"></i>Logout
                    </a>
                `;

                //  Citizen users
                if (data.role === 'citizen') {
                    authNav.insertAdjacentHTML('beforebegin', `
                        <li class="nav-item">
                        <a class="nav-link" href="/register_land">
                         <i class="fas fa-plus-circle me-1"></i>Register Land
                        </a>
                        </li>
                    `);
                }

                //  Admins
                if (data.role === 'admin' || data.role === 'super_admin') {
                    authNav.insertAdjacentHTML('beforebegin', `
                        <li class="nav-item">
                           <a class="nav-link" href="/admin_dashboard">
                              <i class="fas fa-tachometer-alt me-1"></i>Admin Dashboard
                          </a>
                        </li>
                    `);
                }

            } else {
                // Not logged in
                authNav.innerHTML = `
                    <a class="nav-link" href="/login">
                        <i class="fas fa-sign-in-alt me-1"></i>Login
                    </a>
                `;
            }
        })
        .catch(error => {
            console.error('Auth check failed:', error);
            authNav.innerHTML = `
                <a class="nav-link" href="/login">
                    <i class="fas fa-sign-in-alt me-1"></i>Login
                </a>
            `;
        });
});
