
console.log("LOGIN_URL====", LOGIN_URL)
const loginForm =
document.getElementById("loginForm");

loginForm.addEventListener(
    "submit",
    async (e) => {

    e.preventDefault();

    const payload = {

        email:
            document.getElementById("email").value,

        password:
            document.getElementById("password").value

    };

    console.log(payload);

    try {

        const response = await fetch(LOGIN_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",

            body: JSON.stringify(payload)

        });

        const data = await response.json();

        console.log(data);
        localStorage.setItem(
            "access_token",
            data.access_token
        )
        if (!response.ok) {

            alert(
                data.detail ||
                "Invalid credentials"
            );

            return;
        }

        alert("Login successful");

        window.location.href=HOME_PAGE;

    } catch (error) {

        console.error(error);

        alert("Server error");

    }

});
