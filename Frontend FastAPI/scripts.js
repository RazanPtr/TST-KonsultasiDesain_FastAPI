document.addEventListener('DOMContentLoaded', function () {
    const sign_in_btn = document.querySelector("#sign-in-btn");
    const sign_up_btn = document.querySelector("#sign-up-btn");
    const container = document.querySelector(".container");
    const signInForm = document.querySelector(".sign-in-form");
    const signUpForm = document.querySelector(".sign-up-form");
    const notificationElement = document.getElementById('notification');

    sign_up_btn.addEventListener("click", () => {
    container.classList.add("sign-up-mode");
    });

    sign_in_btn.addEventListener("click", () => {
    container.classList.remove("sign-up-mode");
    });

    function showNotification(message) {
        notificationElement.textContent = message;
        notificationElement.style.backgroundColor = '#f8d7da';
        notificationElement.style.borderColor = '#f5c6cb';
        notificationElement.style.display = 'block';

        setTimeout(function () {
            notificationElement.style.display = 'none';
        }, 2000);
    }

    function showNotificationOk(message) {
        notificationElement.textContent = message;
        notificationElement.style.backgroundColor = '#d4edda';
        notificationElement.style.borderColor = '#c3e6cb';
        notificationElement.style.color = '#155724';
        notificationElement.style.display = 'block';

        setTimeout(function () {
            notificationElement.style.display = 'none';
        }, 2000);
    }

    signInForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("username-login").value;
        const password = document.getElementById("password-login").value;
    
        if (!username || !password) {
        showNotification("Please fill in both username and password.");
        return;
        }
    
        try {
        const response = await fetch("https://desain-psikologi-fastapi.whitecliff-184c41f4.southeastasia.azurecontainerapps.io/token", {
            method: "POST",
            headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            },
            body: `username=${username}&password=${password}`,
        });
    
        if (response.ok) {
            showNotificationOk("Welcome to design service")
            window.location.href = "https://desain-psikologi-fastapi.whitecliff-184c41f4.southeastasia.azurecontainerapps.io/docs";
            document.getElementById("username-login").value = "";
                document.getElementById("password-login").value = "";
        } else {
            const errorData = await response.json();
            showNotification("Invalid username or password");
        }
        } catch (error) {
        console.error("Error during login:", error.message);
        }
    });

    signUpForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("username-signup").value;
        const password = document.getElementById("password-signup").value;

        // Check if username and password are not empty
        if (!username || !password) {
            showNotification("Please fill in both username and password.");
            return;
        }

        const formData = new FormData();
        formData.append("username", username);
        formData.append("password", password);
        try {
            const response = await fetch("https://desain-psikologi-fastapi.whitecliff-184c41f4.southeastasia.azurecontainerapps.io/users", {
                method: "POST",
                headers: {
                    // Change Content-Type to "application/x-www-form-urlencoded"
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                body: new URLSearchParams(formData),
            });

            if (response.ok) {
                // User registered successfully, show success message
                showNotificationOk("User registered successfully.");

                // Redirect to sign-in page
                container.classList.remove("sign-up-mode");

                // Clear input fields
                document.getElementById("username-signup").value = "";
                document.getElementById("password-signup").value = "";
            } else {
                // Registration failed, show error message
                showNotification("Registration failed. Please try again.");
            }
        } catch (error) {
            console.error("Error during registration:", error.message);
        }
    });
});