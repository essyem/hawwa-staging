// Enhanced Admin Scripts - Microsoft Exchange Admin inspired
document.addEventListener('DOMContentLoaded', function() {
    
    // Sidebar functionality
    initSidebar();
    
    // Search functionality
    initSearch();
    
    // Theme management
    initTheme();
    
    // Navigation state management
    initNavigation();
    
    // Tooltips and popovers
    initTooltips();
    
    // Auto-save forms
    initAutoSave();
});

// Sidebar Management
function initSidebar() {
    const sidebar = document.getElementById('adminSidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const collapseBtn = document.getElementById('sidebarCollapseBtn');
    const mainContent = document.querySelector('.admin-main');
    
    // Load sidebar state from localStorage
    const sidebarState = localStorage.getItem('adminSidebarState') || 'expanded';
    if (sidebarState === 'collapsed') {
        sidebar?.classList.add('collapsed');
    } else if (sidebarState === 'hidden' && window.innerWidth <= 1024) {
        sidebar?.classList.remove('show');
    }
    
    // Toggle sidebar (mobile)
    sidebarToggle?.addEventListener('click', function() {
        if (window.innerWidth <= 1024) {
            sidebar?.classList.toggle('show');
        } else {
            toggleSidebarCollapse();
        }
    });
    
    // Collapse/expand sidebar (desktop)
    collapseBtn?.addEventListener('click', function() {
        toggleSidebarCollapse();
    });
    
    function toggleSidebarCollapse() {
        if (sidebar) {
            const isCollapsed = sidebar.classList.contains('collapsed');
            if (isCollapsed) {
                sidebar.classList.remove('collapsed');
                localStorage.setItem('adminSidebarState', 'expanded');
                collapseBtn.innerHTML = '<i class="fas fa-angle-left"></i>';
            } else {
                sidebar.classList.add('collapsed');
                localStorage.setItem('adminSidebarState', 'collapsed');
                collapseBtn.innerHTML = '<i class="fas fa-angle-right"></i>';
            }
        }
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 1024) {
            sidebar?.classList.remove('show');
        }
    });
    
    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 1024 && 
            sidebar?.classList.contains('show') &&
            !sidebar.contains(e.target) && 
            !sidebarToggle?.contains(e.target)) {
            sidebar.classList.remove('show');
        }
    });
}

// Search Functionality
function initSearch() {
    const searchInput = document.querySelector('.admin-search');
    let searchTimeout;
    
    searchInput?.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length > 2) {
            searchTimeout = setTimeout(() => {
                performSearch(query);
            }, 300);
        }
    });
    
    searchInput?.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            performSearch(this.value.trim());
        }
    });
}

function performSearch(query) {
    console.log('Searching for:', query);
    // Implement search functionality here
    // This could integrate with your backend search API
    
    // Example: highlight navigation items that match
    highlightSearchResults(query);
}

function highlightSearchResults(query) {
    const navLinks = document.querySelectorAll('.nav-link, .nav-toggle');
    const searchTerm = query.toLowerCase();
    
    navLinks.forEach(link => {
        const text = link.textContent.toLowerCase();
        link.classList.remove('search-highlight');
        
        if (text.includes(searchTerm)) {
            link.classList.add('search-highlight');
        }
    });
}

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('adminTheme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Theme toggle functionality can be added here
    const themeToggle = document.querySelector('[data-theme-toggle]');
    themeToggle?.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('adminTheme', newTheme);
    });
}

// Navigation State Management
function initNavigation() {
    // Save active navigation state
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            
            // Expand parent section if nested
            const parentCollapse = link.closest('.collapse');
            if (parentCollapse) {
                parentCollapse.classList.add('show');
                const toggleBtn = document.querySelector(`[data-bs-target="#${parentCollapse.id}"]`);
                if (toggleBtn) {
                    toggleBtn.setAttribute('aria-expanded', 'true');
                }
            }
        }
    });
    
    // Handle navigation section toggles
    const navToggles = document.querySelectorAll('.nav-toggle');
    navToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const targetId = this.getAttribute('data-bs-target');
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            
            // Save state
            if (targetId) {
                localStorage.setItem(`navSection_${targetId}`, isExpanded ? 'false' : 'true');
            }
        });
    });
    
    // Restore navigation states
    navToggles.forEach(toggle => {
        const targetId = toggle.getAttribute('data-bs-target');
        if (targetId) {
            const savedState = localStorage.getItem(`navSection_${targetId}`);
            if (savedState === 'false') {
                const target = document.querySelector(targetId);
                if (target) {
                    target.classList.remove('show');
                    toggle.setAttribute('aria-expanded', 'false');
                }
            }
        }
    });
}

// Initialize Tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Auto-save Forms
function initAutoSave() {
    const forms = document.querySelectorAll('[data-auto-save]');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        let saveTimeout;
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                clearTimeout(saveTimeout);
                showSaveIndicator('saving');
                
                saveTimeout = setTimeout(() => {
                    autoSaveForm(form);
                }, 1000);
            });
        });
    });
}

function autoSaveForm(form) {
    const formData = new FormData(form);
    const url = form.getAttribute('data-auto-save') || form.action;
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSaveIndicator('saved');
        } else {
            showSaveIndicator('error');
        }
    })
    .catch(error => {
        console.error('Auto-save error:', error);
        showSaveIndicator('error');
    });
}

function showSaveIndicator(status) {
    const indicator = document.querySelector('.save-indicator') || createSaveIndicator();
    
    indicator.className = `save-indicator ${status}`;
    
    switch (status) {
        case 'saving':
            indicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            break;
        case 'saved':
            indicator.innerHTML = '<i class="fas fa-check"></i> Saved';
            setTimeout(() => indicator.classList.add('fade-out'), 2000);
            break;
        case 'error':
            indicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Save failed';
            break;
    }
}

function createSaveIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'save-indicator';
    indicator.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        font-size: 0.875rem;
        z-index: 1060;
        transition: all 0.3s ease;
    `;
    document.body.appendChild(indicator);
    return indicator;
}

// Utility Functions
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 80px;
        right: 20px;
        z-index: 1060;
        min-width: 300px;
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

function loadWithSpinner(element, url, callback = null) {
    element.classList.add('loading');
    
    fetch(url)
        .then(response => response.text())
        .then(html => {
            element.innerHTML = html;
            element.classList.remove('loading');
            if (callback) callback();
        })
        .catch(error => {
            console.error('Load error:', error);
            element.classList.remove('loading');
            element.innerHTML = '<div class="alert alert-danger">Failed to load content</div>';
        });
}

// Export functions for global use
window.adminUtils = {
    showNotification,
    confirmAction,
    loadWithSpinner,
    performSearch
};

// Additional CSS for search highlighting
const additionalCSS = `
.search-highlight {
    background: rgba(0, 120, 212, 0.1) !important;
    color: var(--admin-primary) !important;
}

.save-indicator.saving {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
}

.save-indicator.saved {
    background: #d1f2eb;
    border-left: 4px solid #28a745;
}

.save-indicator.error {
    background: #f8d7da;
    border-left: 4px solid #dc3545;
}

.save-indicator.fade-out {
    opacity: 0;
    transform: translateX(100%);
}
`;

// Add additional CSS to head
if (!document.querySelector('#admin-dynamic-styles')) {
    const style = document.createElement('style');
    style.id = 'admin-dynamic-styles';
    style.textContent = additionalCSS;
    document.head.appendChild(style);
}