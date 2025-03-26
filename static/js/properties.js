/*=============== CHANGE BACKGROUND HEADER ===============*/
const scrollHeader = () => {
    const header = document.getElementById('header');
    window.scrollY >= 50 ? header.classList.add('scroll-header')
                         : header.classList.remove('scroll-header');
};
window.addEventListener('scroll', scrollHeader);

/*=============== PROPERTIES PAGINATION AND RENDERING ===============*/
document.addEventListener('DOMContentLoaded', function () {

    



    // DOM Elements
    const propertiesContainer = document.getElementById('properties-container');
    const paginationContainer = document.getElementById('pagination');
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const propertyTypeSelect = document.getElementById('property-type');
    const stateSelect = document.getElementById('state');
    const citySelect = document.getElementById('city');
    const minPriceInput = document.getElementById('min-price');
    const maxPriceInput = document.getElementById('max-price');
    const applyFiltersButton = document.getElementById('apply-filters');
    const resetFiltersButton = document.getElementById('reset-filters');
    const toggleFiltersButton = document.getElementById('toggle-filters');
    const filtersContainer = document.getElementById('filters-container');
    const priceErrorsContainer = document.getElementById('price-errors');

    const urlParams = new URLSearchParams(window.location.search);

    // Check if 'search' parameter exists
    if (urlParams.has('search')) {
        const searchTerm = urlParams.get('search');
        searchInput.value = searchTerm;
        searchButton.click();
    }
    
    // State variables
    let currentPage = 1;
    let allProperties = [];
    let activeFilters = {
        search: document.getElementById('search-input').value.trim(),
        propertyType: '',
        state: '',
        city: '',
        minPrice: '',
        maxPrice: ''
    };

    // Initialize the page
    initPage();

    async function initPage() {
        await fetchFilterOptions();
        fetchProperties(currentPage, activeFilters);
        setupEventListeners();
    }

    // Fetch filter options
    async function fetchFilterOptions() {
        try {
            const response = await fetch('/filter-options');
            if (response.ok) {
                const data = await response.json();
                filterOptions = data;
                populateFilterOptions();
            } else {
                console.error('Failed to fetch filter options');
            }
        } catch (error) {
            console.error('Error fetching filter options:', error);
        }
    }

    // Populate filter dropdowns
    function populateFilterOptions() {
        // Property Types
        propertyTypeSelect.innerHTML = '<option value="">All Types</option>';
        filterOptions.propertyTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type.property_type_id;
            option.textContent = type.property_type_name;
            propertyTypeSelect.appendChild(option);
        });

        // States
        stateSelect.innerHTML = '<option value="">All States</option>';
        filterOptions.states.forEach(state => {
            const option = document.createElement('option');
            option.value = state.state_id;
            option.textContent = state.state_name;
            stateSelect.appendChild(option);
        });

        // Cities (populated when state is selected)
        stateSelect.addEventListener('change', function() {
            const stateId = this.value;
            citySelect.innerHTML = '<option value="">All Cities</option>';
            citySelect.disabled = !stateId;
            
            if (stateId) {
                const cities = filterOptions.cities.filter(city => city.state_id == stateId);
                cities.forEach(city => {
                    const option = document.createElement('option');
                    option.value = city.city_id;
                    option.textContent = city.city_name;
                    citySelect.appendChild(option);
                });
            }
        });
    }

    // Set up event listeners
    function setupEventListeners() {
        // Search button
        document.getElementById('search-button').addEventListener('click', function() {
            currentPage = 1;
            updateActiveFilters();
            fetchProperties(currentPage, activeFilters);
        });

        // Apply filters button
        document.getElementById('apply-filters').addEventListener('click', function() {
            currentPage = 1;
            updateActiveFilters();
            fetchProperties(currentPage, activeFilters);
        });
        // Apply filters
        applyFiltersButton.addEventListener('click', function() {
            if (!validatePriceInputs()) return;
            currentPage = 1;
            updateActiveFilters();
            fetchProperties(currentPage, activeFilters);
            collapseFilters();
        });

        // Reset filters
        resetFiltersButton.addEventListener('click', function() {
            searchInput.value = '';
            propertyTypeSelect.value = '';
            stateSelect.value = '';
            citySelect.innerHTML = '<option value="">All Cities</option>';
            citySelect.disabled = true;
            minPriceInput.value = '';
            maxPriceInput.value = '';
            clearPriceErrors();
            
            currentPage = 1;
            activeFilters = {
                search: '',
                propertyType: '',
                state: '',
                city: '',
                minPrice: '',
                maxPrice: ''
            };
            fetchProperties(currentPage);
            collapseFilters();
        });

        // Search functionality
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                currentPage = 1;
                updateActiveFilters();
                fetchProperties(currentPage, activeFilters);
            }
        });

        searchButton.addEventListener('click', function() {
            currentPage = 1;
            updateActiveFilters();
            fetchProperties(currentPage, activeFilters);
        });

        // Toggle filters
        toggleFiltersButton.addEventListener('click', toggleFilters);

        // Price validation
        minPriceInput.addEventListener('input', validatePriceInputs);
        maxPriceInput.addEventListener('input', validatePriceInputs);
        minPriceInput.addEventListener('blur', validatePriceInputs);
        maxPriceInput.addEventListener('blur', validatePriceInputs);
    }

    // Price validation
    function validatePriceInputs() {
        const minPrice = minPriceInput.value.trim();
        const maxPrice = maxPriceInput.value.trim();
        let isValid = true;
        let errorMessage = '';

        // Clear previous errors
        clearPriceErrors();

        // Validate min price
        if (minPrice) {
            const minValue = parseFloat(minPrice);
            if (isNaN(minValue)) {
                errorMessage = 'Min price must be a number';
                isValid = false;
            } else if (minValue < 0) {
                errorMessage = 'Min price must be positive';
                isValid = false;
            }
        }

        // Validate max price
        if (maxPrice) {
            const maxValue = parseFloat(maxPrice);
            if (isNaN(maxValue)) {
                errorMessage = 'Max price must be a number';
                isValid = false;
            } else if (maxValue < 0) {
                errorMessage = 'Max price must be positive';
                isValid = false;
            }
        }

        // Validate range
        if (minPrice && maxPrice && isValid) {
            const minValue = parseFloat(minPrice);
            const maxValue = parseFloat(maxPrice);
            if (minValue > maxValue) {
                errorMessage = 'Max price must be ≥ min price';
                isValid = false;
            }
        }

        if (!isValid) {
            priceErrorsContainer.textContent = errorMessage;
            minPriceInput.style.borderColor = 'red';
            maxPriceInput.style.borderColor = 'red';
        }

        return isValid;
    }

    function clearPriceErrors() {
        priceErrorsContainer.textContent = '';
        minPriceInput.style.borderColor = '';
        maxPriceInput.style.borderColor = '';
    }

    // Toggle filters visibility
    function toggleFilters() {
        if (filtersContainer.style.display === 'none') {
            filtersContainer.style.display = 'block';
            toggleFiltersButton.innerHTML = '<i class="bx bx-filter-alt"></i> Hide Filters';
        } else {
            collapseFilters();
        }
    }

    function collapseFilters() {
        filtersContainer.style.display = 'none';
        toggleFiltersButton.innerHTML = '<i class="bx bx-filter-alt"></i> Filters';
    }

    // Update active filters
    function updateActiveFilters() {
        activeFilters = {
            search: document.getElementById('search-input').value.trim(),
            propertyType: document.getElementById('property-type').value,
            state: document.getElementById('state').value,
            city: document.getElementById('city').value,
            minPrice: document.getElementById('min-price').value,
            maxPrice: document.getElementById('max-price').value
        };
    }

    // Fetch properties with filters
    function fetchProperties(page = 1, filters = {}) {
        const formData = new FormData();
        
        // Add all filter parameters
        if (filters.search) formData.append('search', filters.search);
        if (filters.propertyType) formData.append('property_type', filters.propertyType);
        if (filters.state) formData.append('state', filters.state);
        if (filters.city) formData.append('city', filters.city);
        if (filters.minPrice) formData.append('min_price', filters.minPrice);
        if (filters.maxPrice) formData.append('max_price', filters.maxPrice);
        formData.append('page', page);
        
        fetch('/properties-data', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                allProperties = data.properties;
                renderProperties();
                renderPagination(data.total, data.pages, page);
            } else {
                showNoResults(data.message || 'No properties found');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNoResults('Error loading properties');
        });
    }

    function showNoResults() {
        propertiesContainer.innerHTML = '<p class="no-results">No properties found matching your criteria.</p>';
        paginationContainer.innerHTML = '';
    }

    // Create property card HTML
    function createPropertyCard(property) {
        return `
            <article class="properties__card" onclick="window.location.href='/property_details?property_id=${property.property_id}'">
                <img src="static/${property.image_url}" alt="${property.title}" class="properties__img">
                <div class="properties__data">
                    <h2 class="properties__price"><span>₹${Number(property.price).toLocaleString()}</span></h2>
                    <h3 class="properties__title">${property.title}</h3>
                    <p class="properties__description">${property.description.substring(0, 100)}...</p>
                </div>
            </article>
        `;
    }

    // Render properties
    function renderProperties() {
        propertiesContainer.innerHTML = '';
        
        if (allProperties.length === 0) {
            showNoResults();
            return;
        }

        allProperties.forEach(property => {
            propertiesContainer.innerHTML += createPropertyCard(property);
        });
    }

    // Render pagination
    function renderPagination(totalItems, totalPages, currentPage) {
        paginationContainer.innerHTML = '';
        
        if (totalPages <= 1) return;

        // Previous button
        const prevButton = document.createElement('button');
        prevButton.innerHTML = '&laquo;';
        prevButton.disabled = currentPage === 1;
        prevButton.addEventListener('click', () => {
            if (currentPage > 1) {
                fetchProperties(currentPage - 1, activeFilters);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
        paginationContainer.appendChild(prevButton);

        // Page buttons
        for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= currentPage - 1 && i <= currentPage + 1)) {
                const pageButton = document.createElement('button');
                pageButton.textContent = i;
                if (i === currentPage) {
                    pageButton.classList.add('active');
                    pageButton.disabled = true;
                }
                pageButton.addEventListener('click', () => {
                    fetchProperties(i, activeFilters);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                });
                paginationContainer.appendChild(pageButton);
                
                if (i === 1 && currentPage > 3) {
                    paginationContainer.appendChild(createEllipsis());
                }
                if (i === currentPage + 1 && i < totalPages - 1) {
                    paginationContainer.appendChild(createEllipsis());
                }
            }
        }

        // Next button
        const nextButton = document.createElement('button');
        nextButton.innerHTML = '&raquo;';
        nextButton.disabled = currentPage === totalPages;
        nextButton.addEventListener('click', () => {
            if (currentPage < totalPages) {
                fetchProperties(currentPage + 1, activeFilters);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
        paginationContainer.appendChild(nextButton);
    }

    function createEllipsis() {
        const ellipsis = document.createElement('span');
        ellipsis.textContent = '...';
        return ellipsis;
    }

    /*=============== SCROLL SECTIONS ACTIVE LINK ===============*/
    const sections = document.querySelectorAll('section[id]');

    function scrollActive() {
        const scrollY = window.pageYOffset;
        sections.forEach(current => {
            const sectionHeight = current.offsetHeight;
            const sectionTop = current.offsetTop - 58;
            const sectionId = current.getAttribute('id');
            const link = document.querySelector(`.nav__menu a[href*=${sectionId}]`);
            
            if (scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
                link.classList.add('active-link');
            } else {
                link.classList.remove('active-link');
            }
        });
    }
    window.addEventListener('scroll', scrollActive);

    /*=============== SHOW SCROLL UP ===============*/
    const scrollUp = () => {
        const scrollUp = document.getElementById('scroll-up');
        window.scrollY >= 350 ? scrollUp.classList.add('show-scroll')
                              : scrollUp.classList.remove('show-scroll');
    };
    window.addEventListener('scroll', scrollUp);

    /*=============== DARK LIGHT THEME ===============*/
    const themeButton = document.getElementById('theme-button');
    const darkTheme = 'dark-theme';
    const iconTheme = 'bx-sun';

    const selectedTheme = localStorage.getItem('selected-theme');
    const selectedIcon = localStorage.getItem('selected-icon');

    if (selectedTheme) {
        document.body.classList[selectedTheme === 'dark' ? 'add' : 'remove'](darkTheme);
        themeButton.classList[selectedIcon === 'bx bx-moon' ? 'add' : 'remove'](iconTheme);
    }

    themeButton.addEventListener('click', () => {
        document.body.classList.toggle(darkTheme);
        themeButton.classList.toggle(iconTheme);
        localStorage.setItem('selected-theme', document.body.classList.contains(darkTheme) ? 'dark' : 'light');
        localStorage.setItem('selected-icon', themeButton.classList.contains(iconTheme) ? 'bx bx-moon' : 'bx bx-sun');
    });

    /*=============== SCROLL REVEAL ANIMATION ===============*/
    const sr = ScrollReveal({
        origin: 'top',
        distance: '60px',
        duration: 2500,
        delay: 400,
    });

    sr.reveal('.properties__container, .footer__container');
    sr.reveal('.footer__info', { delay: 500 });
});