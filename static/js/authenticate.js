const container = document.querySelector('.container');
const registerBtn = document.querySelector('.register-btn');
const loginBtn = document.querySelector('.login-btn');

// Function to show the registration form
registerBtn.addEventListener('click', () => {
    container.classList.add('active'); // Add active class to show the register form
    document.getElementById('register').style.display = 'block'; // Show registration form
    document.getElementById('login').style.display = 'none'; // Hide login form
});

// Function to show the login form
loginBtn.addEventListener('click', () => {
    container.classList.remove('active'); // Remove active class to show the login form
    document.getElementById('register').style.display = 'none'; // Hide registration form
    document.getElementById('login').style.display = 'block'; // Show login form
});

// On page load, check if an error message is present and determine which form to show
document.addEventListener("DOMContentLoaded", function () {
    const loginError = "{{ login_error }}"; // Get login error from Flask
    const registerError = "{{ register_error }}"; // Get register error from Flask

    // Show the appropriate form based on the error type
    if (registerError) {
        document.getElementById('register').style.display = 'block'; // Show register form
        document.getElementById('login').style.display = 'none'; // Hide login form
        container.classList.add('active'); // Add active class to show register form
    } else if (loginError) {
        document.getElementById('login').style.display = 'block'; // Show login form
        document.getElementById('register').style.display = 'none'; // Hide register form
        container.classList.remove('active'); // Ensure login form is not marked active
    } else {
        document.getElementById('login').style.display = 'block'; // Default to show login form
        document.getElementById('register').style.display = 'none'; // Ensure register form is hidden
    }
});
