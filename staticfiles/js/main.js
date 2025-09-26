/**
 * Main JavaScript for Hawwa Postpartum Care
 */

// Import or include services.js
// Note: This is a comment reminder. In real implementation, 
// you would include the file in your base template.

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            if(this.getAttribute('href') === '#') return;
            
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Add active class to nav links based on current page
    const currentLocation = location.href;
    const menuItems = document.querySelectorAll('.navbar-nav a.nav-link');
    
    menuItems.forEach(link => {
        if(link.href === currentLocation) {
            link.classList.add('active');
        }
    });
    
    // Form validation styles
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Booking date picker initialization (if exists)
    const bookingDatePicker = document.getElementById('booking-date');
    if(bookingDatePicker) {
        // Add date picker initialization code here
        // This is just a placeholder for actual date picker integration
        console.log('Date picker would be initialized here');
    }
    
    // Service filter functionality (if exists)
    const serviceFilters = document.querySelectorAll('.service-filter');
    if(serviceFilters.length > 0) {
        serviceFilters.forEach(filter => {
            filter.addEventListener('click', function() {
                const filterValue = this.getAttribute('data-filter');
                
                // Remove active class from all filters
                serviceFilters.forEach(f => f.classList.remove('active'));
                
                // Add active class to current filter
                this.classList.add('active');
                
                // Filter the service items
                const serviceItems = document.querySelectorAll('.service-item');
                
                serviceItems.forEach(item => {
                    if(filterValue === 'all') {
                        item.style.display = 'block';
                    } else if(item.classList.contains(filterValue)) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        });
    }
    
    // AI Buddy chat functionality (if exists)
    const chatForm = document.getElementById('ai-buddy-form');
    const chatMessages = document.getElementById('chat-messages');
    
    if(chatForm && chatMessages) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const messageInput = this.querySelector('input[name="message"]');
            const message = messageInput.value.trim();
            
            if(message) {
                // Add user message to chat
                addMessageToChat('user', message);
                
                // Clear input
                messageInput.value = '';
                
                // In a real app, you would send this to your backend/API
                // and get a response. This is just a simulation.
                setTimeout(() => {
                    addMessageToChat('bot', 'This is a simulated response from the AI Buddy. In a real implementation, this would be connected to your AI service.');
                    
                    // Scroll to bottom of chat
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }, 1000);
            }
        });
        
        function addMessageToChat(type, text) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('chat-message');
            
            if(type === 'user') {
                messageDiv.classList.add('user-message');
            } else {
                messageDiv.classList.add('bot-message');
            }
            
            messageDiv.textContent = text;
            chatMessages.appendChild(messageDiv);
            
            // Scroll to bottom of chat
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
});

// Theme toggle accessibility wiring (keeps aria-pressed and icon in sync)
(function() {
    function setToggleState(isDark) {
        const toggle = document.getElementById('theme-toggle');
        const icon = document.getElementById('theme-icon');
        if (!toggle || !icon) return;

        toggle.setAttribute('aria-pressed', isDark ? 'true' : 'false');
        // Update icon classes (uses Font Awesome classes already in use)
        if (isDark) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    }

    // Initialize state from qatarTheme if available, else from data-theme attribute
    document.addEventListener('DOMContentLoaded', function() {
        const currentTheme = (window.qatarTheme && window.qatarTheme.currentTheme) || document.documentElement.getAttribute('data-theme') || 'light';
        setToggleState(currentTheme === 'dark');

        const toggle = document.getElementById('theme-toggle');
        if (toggle) {
            toggle.addEventListener('click', function() {
                // If QatarTheme exists, use its toggle to keep behavior consistent
                if (window.qatarTheme && typeof window.qatarTheme.toggleTheme === 'function') {
                    window.qatarTheme.toggleTheme();
                } else {
                    // Fallback: toggle data-theme attribute
                    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
                    document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
                    setToggleState(!isDark);
                }
            });
        }

        // Listen for themeChanged events from qatar-theme.js
        document.addEventListener('themeChanged', function(e) {
            setToggleState(e.detail && e.detail.theme === 'dark');
        });
    });
})();

// Sidebar toggle and responsive behavior
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        const sidebar = document.getElementById('left-sidebar');
        const toggle = document.getElementById('sidebar-toggle');
            const pinBtn = document.getElementById('hawwa-sidebar-pin');
            const miniStrip = document.getElementById('hawwa-mini-strip');
        if(!sidebar || !toggle) return;

        // Initialize state
        const saved = localStorage.getItem('hawwa_sidebar_collapsed');
        const collapsed = saved === 'true';
        function setCollapsed(c) {
            if(c) {
                sidebar.classList.add('collapsed');
                sidebar.style.width = '56px';
                document.documentElement.classList.add('sidebar-collapsed');
                toggle.setAttribute('aria-expanded', 'false');
            } else {
                sidebar.classList.remove('collapsed');
                sidebar.style.width = '220px';
                document.documentElement.classList.remove('sidebar-collapsed');
                toggle.setAttribute('aria-expanded', 'true');
            }
            localStorage.setItem('hawwa_sidebar_collapsed', c ? 'true' : 'false');
        }
        setCollapsed(collapsed);

        toggle.addEventListener('click', function() {
            const isCollapsed = sidebar.classList.contains('collapsed');
            setCollapsed(!isCollapsed);
        });

        // Close desktop sidebar on small screens via CSS media query
        window.matchMedia('(max-width: 991px)').addEventListener('change', function(e) {
            if(e.matches) {
                // small screen
                sidebar.classList.add('d-none');
            } else {
                sidebar.classList.remove('d-none');
            }
        });
    });
})();

    // Sidebar pin/hide handle behavior (desktop only)
    (function() {
        document.addEventListener('DOMContentLoaded', function() {
            const root = document.documentElement;
            const sidebar = document.getElementById('left-sidebar');
            const pinBtn = document.getElementById('hawwa-sidebar-pin');
            const pinIcon = document.getElementById('hawwa-sidebar-pin-icon');
            const handleBtn = document.getElementById('hawwa-sidebar-handle');
            const miniStrip = document.getElementById('hawwa-mini-strip');

            // Only apply this behavior on desktop viewports (match CSS breakpoint)
            const desktopQuery = window.matchMedia('(min-width: 992px)');

            const KEY = 'hawwa_sidebar_pinned';

            function isPinned() {
                return localStorage.getItem(KEY) === 'true';
            }

            function applyState() {
                if(!desktopQuery.matches) {
                    // On small screens, remove desktop classes and don't show mini-strip
                    root.classList.remove('hawwa-sidebar-pinned', 'hawwa-sidebar-hidden');
                    if(miniStrip) miniStrip.style.display = 'none';
                    return;
                }

                if(isPinned()) {
                    root.classList.add('hawwa-sidebar-pinned');
                    root.classList.remove('hawwa-sidebar-hidden');
                    if(pinBtn) pinBtn.setAttribute('aria-pressed', 'true');
                    if(pinIcon) pinIcon.classList.add('text-primary');
                    if(miniStrip) miniStrip.style.display = 'none';
                } else {
                    root.classList.remove('hawwa-sidebar-pinned');
                    root.classList.add('hawwa-sidebar-hidden');
                    if(pinBtn) pinBtn.setAttribute('aria-pressed', 'false');
                    if(pinIcon) pinIcon.classList.remove('text-primary');
                    if(miniStrip) miniStrip.style.display = 'block';
                }
            }

            // Initialize default if missing
            if(localStorage.getItem(KEY) === null) {
                localStorage.setItem(KEY, 'true');
            }

            // React to viewport changes to re-apply classes appropriately
            desktopQuery.addEventListener('change', function() {
                applyState();
            });

            // Apply initial state
            applyState();

            // Pin/unpin click (guarded)
            if(pinBtn) {
                pinBtn.addEventListener('click', function() {
                    const next = !isPinned();
                    localStorage.setItem(KEY, next ? 'true' : 'false');
                    applyState();
                });
            }

            // Mini-strip clicks should temporarily show the sidebar (if present)
            if(miniStrip) {
                miniStrip.addEventListener('click', function(e) {
                    // If a link was clicked, allow navigation but briefly show the sidebar for context
                    root.classList.remove('hawwa-sidebar-hidden');
                    if(!isPinned()) {
                        setTimeout(() => {
                            root.classList.add('hawwa-sidebar-hidden');
                        }, 5000);
                    }
                });
            }
        });
    })();

// Sidebar section collapse persistence
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        const sections = document.querySelectorAll('.sidebar-section');
        if(!sections.length) return;

        sections.forEach((sec, idx) => {
            const btn = sec.querySelector('.btn-toggle');
            const collapseEl = sec.querySelector('.collapse');
            if(!btn || !collapseEl) return;

            const key = 'hawwa_sidebar_section_' + (idx+1);
            // Restore state
            const saved = localStorage.getItem(key);
            const bsCollapse = new bootstrap.Collapse(collapseEl, {toggle:false});
            if(saved === 'collapsed') {
                bsCollapse.hide();
            } else {
                bsCollapse.show();
            }

            btn.addEventListener('click', function() {
                // small delay to let bootstrap toggle finish
                setTimeout(() => {
                    const isShown = collapseEl.classList.contains('show');
                    localStorage.setItem(key, isShown ? 'expanded' : 'collapsed');
                }, 100);
            });
        });
    });
})();