
    document.addEventListener('DOMContentLoaded', function() {
        const themeToggleBtn = document.getElementById('theme-toggle');
        const layoutToggleBtn = document.getElementById('layout-toggle');
        const htmlElement = document.documentElement; // The <html> element
        const mainContainer = document.querySelector('[data-layout="container"]'); // The main container

        // Function to update icons based on the current theme
        function updateThemeIcons(theme) {
            const sunIcon = themeToggleBtn.querySelector('.fa-sun');
            const moonIcon = themeToggleBtn.querySelector('.fa-moon');

            if (theme === 'dark') {
                sunIcon.classList.remove('d-none');
                moonIcon.classList.add('d-none');
            } else {
                sunIcon.classList.add('d-none');
                moonIcon.classList.remove('d-none');
            }
        }

        // Function to update icons based on the current layout
        function updateLayoutIcons(isFluid) {
            const expandIcon = layoutToggleBtn.querySelector('.fa-expand');
            const compressIcon = layoutToggleBtn.querySelector('.fa-compress');

            if (isFluid) {
                expandIcon.classList.add('d-none');
                compressIcon.classList.remove('d-none');
            } else {
                expandIcon.classList.remove('d-none');
                compressIcon.classList.add('d-none');
            }
        }

        // Check for saved theme preference in localStorage
        let currentTheme = localStorage.getItem('theme') || 'dark';
        htmlElement.setAttribute('data-bs-theme', currentTheme);
        updateThemeIcons(currentTheme);

        // Check for saved layout preference in localStorage
        let isFluidLayout = localStorage.getItem('layout') === 'fluid';
        if (isFluidLayout) {
            mainContainer.classList.remove('container');
            mainContainer.classList.add('container-fluid');
        } else {
            mainContainer.classList.remove('container-fluid');
            mainContainer.classList.add('container');
        }
        updateLayoutIcons(isFluidLayout);

        // Event listener for the theme toggle button
        themeToggleBtn.addEventListener('click', function() {
            // Toggle the theme
            currentTheme = htmlElement.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
            htmlElement.setAttribute('data-bs-theme', currentTheme);

            // Update icons
            updateThemeIcons(currentTheme);

            // Save the user's preference in localStorage
            localStorage.setItem('theme', currentTheme);
        });

        // Event listener for the layout toggle button
        layoutToggleBtn.addEventListener('click', function() {
            // Toggle the layout between fluid and compact
            isFluidLayout = !isFluidLayout;

            if (isFluidLayout) {
                mainContainer.classList.remove('container');
                mainContainer.classList.add('container-fluid');
                localStorage.setItem('layout', 'fluid');
            } else {
                mainContainer.classList.remove('container-fluid');
                mainContainer.classList.add('container');
                localStorage.setItem('layout', 'compact');
            }

            // Update icons for layout
            updateLayoutIcons(isFluidLayout);
            location.reload();
        });
    });

