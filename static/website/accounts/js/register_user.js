




const registerForm =
document.getElementById("registerForm");

registerForm.addEventListener(
    "submit",
    async (e) => {

    e.preventDefault();

    const payload = {

        email:
            document.getElementById("email").value,

        password1:
            document.getElementById("password1").value,

        password2:
            document.getElementById("password2").value

    };

    console.log(payload);

    try {

        const response = await fetch(REGISTER_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(payload)

        });

        const data = await response.json();

        console.log(data);

        if (!response.ok) {

            if (Array.isArray(data.detail)) {

                alert(data.detail.join("\n"));

            } else {

                alert(
                    data.detail ||
                    "Registration failed"
                );

            }

            return;
        }

        alert("Account created successfully");

        // redirect
        window.location.href = "/users/login/";

    } catch (error) {

        console.error(error);

        alert("Server error");

    }

});

