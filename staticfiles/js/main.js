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