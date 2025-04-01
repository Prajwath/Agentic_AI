
document.addEventListener("DOMContentLoaded", function () {
    // Toggle Info Dropdown
    const infoIcon = document.getElementById("info-icon");
    const infoDropdown = document.getElementById("info-dropdown");

    if (infoIcon && infoDropdown) {
        infoIcon.addEventListener("click", function () {
            infoDropdown.style.display = infoDropdown.style.display === "block" ? "none" : "block";
        });
    }

    // Toggle Sidebar
    const sidebarToggleButton = document.querySelector(".toggle_button_on");
    const sidebar = document.getElementById("sidebar");

    if (sidebarToggleButton && sidebar) {
        sidebarToggleButton.addEventListener("click", function () {
            sidebar.classList.toggle("open");
        });
    }


    const inputField = document.querySelector(".search-bar");

    const placeholderCarousel = document.querySelector(".placeholder-carousel");

    inputField.addEventListener("input", function () {

        if (inputField.value.trim() !== "") {

            placeholderCarousel.classList.add("placeholder-hidden");

        } else {

            placeholderCarousel.classList.remove("placeholder-hidden");

        }

    });

});
