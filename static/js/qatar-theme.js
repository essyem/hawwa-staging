// Qatar HRMS Theme Enhancement JavaScript
// Enhanced theme system with animations and user experience improvements

class QatarThemeManager {
    constructor() {
        this.themes = ['light', 'dark'];
        this.currentTheme = this.getSavedTheme();
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.setupEventListeners();
        this.addAnimations();
        this.setupAccessibility();
    }

    getSavedTheme() {
        const saved = localStorage.getItem('qatar-hrms-theme');
        if (saved && this.themes.includes(saved)) {
            return saved;
        }
        
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        return 'light';
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.updateThemeIcon(theme);
        this.currentTheme = theme;
        
        // Save preference
        localStorage.setItem('qatar-hrms-theme', theme);
        
        // Dispatch custom event
        document.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: theme }
        }));
        
        // Update theme toggle button state for accessibility
        try {
            const toggle = document.getElementById('theme-toggle');
            const icon = document.getElementById('theme-icon');
            if (toggle) toggle.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
            if (icon) {
                icon.classList.remove('fa-moon', 'fa-sun');
                icon.classList.add(theme === 'dark' ? 'fa-sun' : 'fa-moon');
            }
        } catch (e) {
            // Non-blocking: DOM may not be ready when called; other scripts will sync state
            console.debug('Theme toggle update skipped:', e);
        }
    }

    updateThemeIcon(theme) {
        const themeIcon = document.getElementById('theme-icon');
        if (themeIcon) {
            // Smooth icon transition
            themeIcon.style.transform = 'scale(0.8)';
            
            setTimeout(() => {
                themeIcon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
                themeIcon.style.transform = 'scale(1)';
            }, 150);
        }
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        
        // Add smooth transition effect
        this.addTransitionEffect();
        
        setTimeout(() => {
            this.applyTheme(newTheme);
        }, 100);
    }

    addTransitionEffect() {
        const body = document.body;
        body.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        
        setTimeout(() => {
            body.style.transition = '';
        }, 300);
    }

    setupEventListeners() {
        // Theme toggle button
        const themeToggleBtn = document.querySelector('.theme-toggle');
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', () => this.toggleTheme());
        }

        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('qatar-hrms-theme')) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }

        // Keyboard shortcut (Ctrl/Cmd + Shift + T)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }

    addAnimations() {
        // Add fade-in animation to cards when they come into view
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '50px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe all cards
        document.querySelectorAll('.card').forEach(card => {
            observer.observe(card);
        });

        // Add hover effects to navigation items
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-1px)';
            });

            link.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
    }

    setupAccessibility() {
        // Announce theme changes to screen readers
        const announcer = document.createElement('div');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'sr-only';
        document.body.appendChild(announcer);

        document.addEventListener('themeChanged', (e) => {
            announcer.textContent = `Theme changed to ${e.detail.theme} mode`;
        });

        // Add focus management for theme toggle
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('focus', function() {
                this.style.outline = '2px solid var(--qatar-maroon)';
                this.style.outlineOffset = '2px';
            });

            themeToggle.addEventListener('blur', function() {
                this.style.outline = '';
                this.style.outlineOffset = '';
            });
        }
    }
}

// Enhanced UI Interactions
class QatarUIEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.setupCardAnimations();
        this.setupFormEnhancements();
        this.setupTableEnhancements();
        this.setupButtonEffects();
        this.setupTooltips();
    }

    setupCardAnimations() {
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
                this.style.boxShadow = 'var(--shadow-lg)';
            });

            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = 'var(--shadow-sm)';
            });
        });
    }

    setupFormEnhancements() {
        // Enhanced form focus effects
        document.querySelectorAll('.form-control, .form-select').forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('form-group-focused');
            });

            input.addEventListener('blur', function() {
                this.parentElement.classList.remove('form-group-focused');
            });
        });

        // Form validation feedback
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function(e) {
                const inputs = this.querySelectorAll('.form-control, .form-select');
                inputs.forEach(input => {
                    if (!input.checkValidity()) {
                        input.classList.add('is-invalid');
                    } else {
                        input.classList.remove('is-invalid');
                        input.classList.add('is-valid');
                    }
                });
            });
        });
    }

    setupTableEnhancements() {
        // Enhanced table interactions
        document.querySelectorAll('.table tbody tr').forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.backgroundColor = 'var(--hover-bg)';
            });

            row.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '';
            });
        });
    }

    setupButtonEffects() {
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', function(e) {
                // Ripple effect
                const ripple = document.createElement('span');
                ripple.className = 'ripple';
                
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = x + 'px';
                ripple.style.top = y + 'px';
                
                this.appendChild(ripple);
                
                setTimeout(() => {
                    ripple.remove();
                }, 600);
            });
        });
    }

    setupTooltips() {
        // Simple tooltip implementation
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', function(e) {
                const tooltip = document.createElement('div');
                tooltip.className = 'custom-tooltip';
                tooltip.textContent = this.getAttribute('data-tooltip');
                
                document.body.appendChild(tooltip);
                
                const rect = this.getBoundingClientRect();
                tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
                tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
                
                this.tooltipElement = tooltip;
            });

            element.addEventListener('mouseleave', function() {
                if (this.tooltipElement) {
                    this.tooltipElement.remove();
                    this.tooltipElement = null;
                }
            });
        });
    }
}

// Utility Functions
const QatarUtils = {
    // Format currency with QAR
    formatCurrency(amount, currency = 'QAR') {
        return new Intl.NumberFormat('en-QA', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        }).format(amount);
    },

    // Format dates for Qatar locale
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            timeZone: 'Asia/Qatar'
        };
        return new Intl.DateTimeFormat('en-QA', { ...defaultOptions, ...options }).format(new Date(date));
    },

    // Smooth scroll to element
    scrollTo(element, offset = 0) {
        const target = typeof element === 'string' ? document.querySelector(element) : element;
        if (target) {
            const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - offset;
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    },

    // Show notification
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto remove
        setTimeout(() => {
            notification.classList.add('notification-hide');
            setTimeout(() => notification.remove(), 300);
        }, duration);

        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.classList.add('notification-hide');
            setTimeout(() => notification.remove(), 300);
        });
    },

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            warning: 'exclamation-triangle',
            error: 'times-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme manager
    window.qatarTheme = new QatarThemeManager();
    
    // Initialize UI enhancer
    window.qatarUI = new QatarUIEnhancer();
    
    // Make utils globally available
    window.QatarUtils = QatarUtils;
    
    // Legacy function for backward compatibility
    window.toggleTheme = () => window.qatarTheme.toggleTheme();
});

// Additional CSS for enhanced features
const additionalStyles = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }

    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }

    .custom-tooltip {
        position: absolute;
        background: var(--gray-800);
        color: white;
        padding: 0.5rem 0.75rem;
        border-radius: var(--radius-md);
        font-size: 0.875rem;
        white-space: nowrap;
        z-index: 1000;
        box-shadow: var(--shadow-lg);
        animation: fadeIn 0.2s ease-out;
    }

    [data-theme="dark"] .custom-tooltip {
        background: var(--gray-200);
        color: var(--gray-800);
    }

    .notification {
        position: fixed;
        top: 1rem;
        right: 1rem;
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
        z-index: 1050;
        animation: slideInRight 0.3s ease-out;
        max-width: 300px;
    }

    .notification-content {
        padding: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .notification-close {
        background: none;
        border: none;
        color: var(--text-muted);
        cursor: pointer;
        margin-left: auto;
        font-size: 1.25rem;
    }

    .notification-success {
        border-left: 4px solid var(--success);
    }

    .notification-warning {
        border-left: 4px solid var(--warning);
    }

    .notification-error {
        border-left: 4px solid var(--error);
    }

    .notification-info {
        border-left: 4px solid var(--info);
    }

    .notification-hide {
        animation: slideOutRight 0.3s ease-in;
    }

    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }

    .form-group-focused {
        position: relative;
    }

    .form-group-focused::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--qatar-maroon);
        border-radius: 1px;
        animation: expandWidth 0.3s ease-out;
    }

    @keyframes expandWidth {
        from { width: 0; margin: 0 auto; }
        to { width: 100%; margin: 0; }
    }

    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }
`;

// Inject additional styles
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);
