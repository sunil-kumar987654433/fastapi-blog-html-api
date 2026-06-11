


const postForm = document.getElementById("postForm");

postForm.addEventListener("submit", async (e) => {

    e.preventDefault();
    const payload = {
        title: document.getElementById("title").value,
        content: document.getElementById("content").value,
        // date_posted: new Date().toISOString().split("T")[0],
        // user_id: "{{ current_user.key }}"
    };
    console.log("payload===", payload)
    alert()
    try {

        const response = await fetch(CREATE_POST_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(payload)

        });

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail || "Something went wrong");
            return;
        }

        alert("Post created successfully");

        // close modal
        const modal = bootstrap.Modal.getInstance(
            document.getElementById("postModal")
        );

        modal.hide();

        // optional reload
        window.location.reload();

    } catch (error) {

        console.error(error);

        alert("Server error");

    }

});



const logoutBtn =
document.getElementById("logoutBtn");

if (logoutBtn) {

    logoutBtn.addEventListener(
        "click",
        async () => {

        try {

            await fetch("/logout", {

                method: "POST",

                credentials: "include"

            });

        } catch (error) {

            console.error(error);

        }

        localStorage.removeItem(
            "access_token"
        );

        window.location.href = "/";

    });

}




document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadCurrentUser();

    }
);

async function loadCurrentUser() {

    const guestNavbar =
        document.getElementById(
            "guestNavbar"
        );

    const authNavbar =
        document.getElementById(
            "authNavbar"
        );

    const newPostNavItem =
        document.getElementById(
            "newPostNavItem"
        );

    const navbarUserEmail =
        document.getElementById(
            "navbarUserEmail"
        );

    const navbarUserImage =
        document.getElementById(
            "navbarUserImage"
        );

    // default state
    if (guestNavbar) {

        guestNavbar.classList.remove(
            "d-none"
        );

    }

    if (authNavbar) {

        authNavbar.classList.add(
            "d-none"
        );

    }

    if (newPostNavItem) {

        newPostNavItem.classList.add(
            "d-none"
        );

    }

    const token =
        localStorage.getItem(
            "access_token"
        );

    if (!token) {
        return;
    }

    try {

        const response =
            await fetch(
                "/api/users/me",
            {

            method: "GET",

            headers: {
                Authorization:
                    `Bearer ${token}`
            },

            credentials: "include"

        });

        if (!response.ok) {

            localStorage.removeItem(
                "access_token"
            );

            return;

        }

        const user =
            await response.json();

        console.log(
            "user===",
            user
        );

        // switch navbar
        if (guestNavbar) {

            guestNavbar.classList.add(
                "d-none"
            );

        }

        if (authNavbar) {

            authNavbar.classList.remove(
                "d-none"
            );

        }

        if (newPostNavItem) {

            newPostNavItem.classList.remove(
                "d-none"
            );

        }

        // email
        if (
            navbarUserEmail &&
            user.email
        ) {

            navbarUserEmail.innerText =
                user.email;

        }

        // image
        if (
            navbarUserImage &&
            user.image_path
        ) {

            navbarUserImage.src =
                user.image_path;

        }

    } catch (error) {

        console.error(
            "loadCurrentUser error:",
            error
        );

    }

}

loadCurrentUser();


