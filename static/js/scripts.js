/*!
* Start Bootstrap - Stylish Portfolio v6.0.3 (https://startbootstrap.com/theme/stylish-portfolio)
* Copyright 2013-2021 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-stylish-portfolio/blob/master/LICENSE)
*/
window.addEventListener('DOMContentLoaded', event => {

    const sidebarWrapper = document.getElementById('sidebar-wrapper');
    let scrollToTopVisible = false;
    // Closes the sidebar menu
    const menuToggle = document.body.querySelector('.menu-toggle');
    menuToggle.addEventListener('click', event => {
        event.preventDefault();
        sidebarWrapper.classList.toggle('active');
        _toggleMenuIcon();
        menuToggle.classList.toggle('active');
    })

    /**
     * Adding an event listener to the id_upload_button click object.
     * This should then send a POST to the server.
     */
    document.getElementById("id_upload_button").addEventListener("click", event => {
        console.log("click event listener triggered!", event);
        let inputField = document.getElementById("id_upload_input");
        inputField.click();

        inputField.addEventListener("change", () => {
            console.log("Event listener has been triggered!");
            let files = document.getElementById("id_upload_input").files;
            console.log("files:", files);
            let photo = files[0];
            console.log("photo:", photo);
            let formData = new FormData();

            formData.append("id_image", photo);
            fetch("/api/upload_id", {method: "POST", body: formData})
                .then(response => {
                    console.log("response:", response);
                    if (!response.ok) {
                        alert("User's age was unable to be detected or the user is under 21.");
                    } else {
                        alert("Successfully verified!");
                        $("#id_upload_button").click(e => e.preventDefault());
                        console.log("Successfully verified!");
                    }
                })
                .then(data => console.log("data:", data));
        });
    });

    /**
     * Sign in button event handler
     */

    document.getElementById("login_button").addEventListener("click", event => {
        let username = $("#email_address_input").val();
        if (username == "") {
            alert("Please populate the username field.");
        }

        let formData = new FormData();
        formData.append("username", username);

        fetch("/api/login", {method: "POST", body: formData})
            .then(response => {
                alert("Logged in!");
            });
    });


    // Closes responsive menu when a scroll trigger link is clicked
    var scrollTriggerList = [].slice.call(document.querySelectorAll('#sidebar-wrapper .js-scroll-trigger'));
    scrollTriggerList.map(scrollTrigger => {
        scrollTrigger.addEventListener('click', () => {
            sidebarWrapper.classList.remove('active');
            menuToggle.classList.remove('active');
            _toggleMenuIcon();
        })
    });

    function _toggleMenuIcon() {
        const menuToggleBars = document.body.querySelector('.menu-toggle > .fa-bars');
        const menuToggleTimes = document.body.querySelector('.menu-toggle > .fa-times');
        if (menuToggleBars) {
            menuToggleBars.classList.remove('fa-bars');
            menuToggleBars.classList.add('fa-times');
        }
        if (menuToggleTimes) {
            menuToggleTimes.classList.remove('fa-times');
            menuToggleTimes.classList.add('fa-bars');
        }
    }

    // Scroll to top button appear
    document.addEventListener('scroll', () => {
        const scrollToTop = document.body.querySelector('.scroll-to-top');
        if (document.documentElement.scrollTop > 100) {
            if (!scrollToTopVisible) {
                fadeIn(scrollToTop);
                scrollToTopVisible = true;
            }
        } else {
            if (scrollToTopVisible) {
                fadeOut(scrollToTop);
                scrollToTopVisible = false;
            }
        }
    })
})

function fadeOut(el) {
    el.style.opacity = 1;
    (function fade() {
        if ((el.style.opacity -= .1) < 0) {
            el.style.display = "none";
        } else {
            requestAnimationFrame(fade);
        }
    })();
};

function fadeIn(el, display) {
    el.style.opacity = 0;
    el.style.display = display || "block";
    (function fade() {
        var val = parseFloat(el.style.opacity);
        if (!((val += .1) > 1)) {
            el.style.opacity = val;
            requestAnimationFrame(fade);
        }
    })();
};
