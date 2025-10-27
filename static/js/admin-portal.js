/**
 * Hawwa Admin Portal JavaScript
 * Enhanced functionality for the IFMS-inspired admin portal
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin portal functionality
    initializeSidebar();
    initializeNavigation();
    initializeCards();
    initializeTooltips();
});

/**
 * Initialize sidebar functionality
 */
function initializeSidebar() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');

    if (sidebarToggle && sidebar && content) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            content.classList.toggle('expanded');
            
            // Store preference in localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('hawwa_sidebar_collapsed', isCollapsed);
        });

        // Restore sidebar state from localStorage
        const savedState = localStorage.getItem('hawwa_sidebar_collapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
            content.classList.add('expanded');
        }
    }

    // Mobile sidebar handling
    if (window.innerWidth <= 768) {
        const sidebarOverlay = document.getElementById('sidebarOverlay');
        const adminSidebar = document.getElementById('adminSidebar');

        if (sidebarToggle && adminSidebar) {
            sidebarToggle.addEventListener('click', function() {
                adminSidebar.classList.toggle('show');
                if (sidebarOverlay) {
                    sidebarOverlay.classList.toggle('show');
                }
            });
        }

        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', function() {
                adminSidebar.classList.remove('show');
                sidebarOverlay.classList.remove('show');
            });
        }
    }
}

/**
 * Initialize navigation functionality
 */
function initializeNavigation() {
    // Auto-collapse navigation sections for better UX
    const collapseElements = document.querySelectorAll('[data-bs-toggle="collapse"]');
    
    collapseElements.forEach(element => {
        element.addEventListener('click', function() {
            const targetId = this.getAttribute('data-bs-target');
            const allCollapses = document.querySelectorAll('.nav-submenu.collapse');
            
            // Close other menus when one is opened
            allCollapses.forEach(collapse => {
                if (collapse.id !== targetId.replace('#', '')) {
                    const bsCollapse = bootstrap.Collapse.getInstance(collapse);
                    if (bsCollapse) {
                        bsCollapse.hide();
                    }
                }
            });
        });
    });

    // Highlight active navigation items based on current URL
    highlightActiveNavigation();
}

/**
 * Highlight active navigation items
 */
function highlightActiveNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '#') {
            link.classList.add('active');
            
            // If it's in a submenu, expand the parent menu
            const submenu = link.closest('.nav-submenu');
            if (submenu) {
                const collapse = bootstrap.Collapse.getOrCreateInstance(submenu);
                collapse.show();
            }
        }
    });
}

/**
 * Initialize card animations and interactions
 */
function initializeCards() {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
        // Add subtle hover effects
        card.addEventListener('mouseenter', function() {
            this.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
        });
    });

    // Stats cards animation
    const statsCards = document.querySelectorAll('.card .bg-gradient');
    statsCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.transition = 'transform 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Smooth scroll to top function
 */
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

/**
 * Show loading state for buttons
 */
function showButtonLoading(button, text = 'Loading...') {
    const originalText = button.innerHTML;
    button.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${text}`;
    button.disabled = true;
    
    return function() {
        button.innerHTML = originalText;
        button.disabled = false;
    };
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" id="${toastId}">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Auto-remove after shown
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

/**
 * Search functionality for navigation
 */
function initializeSearch() {
    const searchInput = document.querySelector('.admin-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const navLinks = document.querySelectorAll('.nav-link .nav-text');
            
            navLinks.forEach(link => {
                const text = link.textContent.toLowerCase();
                const navItem = link.closest('.nav-item');
                
                if (text.includes(query) || query === '') {
                    navItem.style.display = '';
                } else {
                    navItem.style.display = 'none';
                }
            });
        });
    }
}

/**
 * Utility function to format numbers
 */
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

/**
 * Utility function to format currency
 */
function formatCurrency(amount, currency = 'QAR') {
    return new Intl.NumberFormat('en-QA', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Global functions for template use
window.hawwaAdmin = {
    scrollToTop,
    showButtonLoading,
    showToast,
    formatNumber,
    formatCurrency
};