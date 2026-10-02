const loginForm = document.getElementById("loginForm");

const userIdInput = document.getElementById("userId");
const passwordInput = document.getElementById("password");

const rememberMe = document.getElementById("rememberMe");
const togglePassword = document.getElementById("togglePassword");

const loginMessage = document.getElementById("loginMessage");

const loginButton = document.getElementById("loginButton");
const loginButtonText = document.getElementById("loginButtonText");


// =========================================================
// SHOW / HIDE PASSWORD
// =========================================================

togglePassword.addEventListener("click", () => {

    const isPassword =
        passwordInput.type === "password";

    passwordInput.type =
        isPassword ? "text" : "password";

    togglePassword.textContent =
        isPassword ? "Hide" : "Show";

});


// =========================================================
// LOGIN
// =========================================================

loginForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    loginMessage.textContent = "";

    loginButton.disabled = true;

    loginButtonText.textContent =
        "Signing in...";


    const userId =
        userIdInput.value.trim();

    const password =
        passwordInput.value;


    try {

        const response = await fetch(
            "/api/auth/login",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    user_id: userId,
                    password: password
                })
            }
        );


        const data =
            await response.json();


        // =================================================
        // LOGIN FAILED
        // =================================================

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Invalid user ID or password."
            );

        }


        // =================================================
        // SAVE LOGIN SESSION
        // =================================================

        const storage =
            rememberMe.checked
                ? localStorage
                : sessionStorage;


        storage.setItem(
            "access_token",
            data.access_token
        );


        storage.setItem(
            "user",
            JSON.stringify(data.user)
        );


        // Remove old session from
        // the other storage type.

        const otherStorage =
            rememberMe.checked
                ? sessionStorage
                : localStorage;


        otherStorage.removeItem(
            "access_token"
        );

        otherStorage.removeItem(
            "user"
        );


        // =================================================
        // ROLE-BASED REDIRECTION
        // =================================================

        if (data.user.role === "ADMIN") {

            window.location.href =
                "/admin/dashboard.html";

        } else {

            window.location.href =
                "/customer/dashboard.html";

        }

    }

    catch (error) {

        loginMessage.textContent =
            error.message;

        loginButton.disabled = false;

        loginButtonText.textContent =
            "Sign In";
    }

});