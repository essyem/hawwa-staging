/**
 * Hawwa Postpartum Care Services JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Service Filter Form Handling
    const filterForm = document.querySelector('.service-filter-form');
    if (filterForm) {
        // Auto-submit on category change
        const categorySelect = filterForm.querySelector('#id_category');
        if (categorySelect) {
            categorySelect.addEventListener('change', function() {
                filterForm.submit();
            });
        }
        
        // Price range slider handling
        const rangeInputs = document.querySelectorAll('.price-range-slider input');
        const progress = document.querySelector('.price-range-slider .progress');
        const minPriceVal = document.querySelector('#min-price-val');
        const maxPriceVal = document.querySelector('#max-price-val');
        
        if (rangeInputs.length && progress && minPriceVal && maxPriceVal) {
            let priceGap = 500; // Minimum gap between handles
            
            rangeInputs.forEach(input => {
                input.addEventListener('input', (e) => {
                    let minVal = parseInt(rangeInputs[0].value);
                    let maxVal = parseInt(rangeInputs[1].value);
                    
                    if (maxVal - minVal < priceGap) {
                        if (e.target.className === "min-range") {
                            rangeInputs[0].value = maxVal - priceGap;
                        } else {
                            rangeInputs[1].value = minVal + priceGap;
                        }
                    } else {
                        minPriceVal.textContent = minVal;
                        maxPriceVal.textContent = maxVal;
                        let percent = (minVal / rangeInputs[0].max) * 100;
                        let percent2 = 100 - (maxVal / rangeInputs[1].max) * 100;
                        progress.style.left = percent + "%";
                        progress.style.right = percent2 + "%";
                    }
                });
            });
        }
    }
    
    // Service Detail Gallery
    const galleryThumbnails = document.querySelectorAll('.gallery-thumbnail');
    if (galleryThumbnails.length) {
        galleryThumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                const imageUrl = this.getAttribute('src');
                const mainImage = document.querySelector('.service-images img:first-child');
                if (mainImage) {
                    mainImage.setAttribute('src', imageUrl);
                }
            });
        });
    }
    
    // Add to Wishlist functionality
    const wishlistButtons = document.querySelectorAll('.add-to-wishlist');
    if (wishlistButtons.length) {
        wishlistButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const serviceId = this.getAttribute('data-service-id');
                
                // Send AJAX request to add to wishlist
                fetch('/accounts/add-to-wishlist/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        service_id: serviceId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update UI to show item was added
                        this.innerHTML = '<i class="fas fa-heart me-1"></i> Added to Wishlist';
                        this.classList.remove('btn-outline-primary');
                        this.classList.add('btn-primary');
                        this.disabled = true;
                        
                        // Show toast notification
                        showToast('Service added to your wishlist!');
                    } else if (data.error === 'login_required') {
                        window.location.href = '/accounts/login/?next=' + window.location.pathname;
                    } else {
                        showToast('Error: ' + data.message, 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('An error occurred. Please try again.', 'danger');
                });
            });
        });
    }
    
    // Service Form Handling
    const serviceForm = document.querySelector('.service-form');
    if (serviceForm) {
        const serviceTypeSelect = document.querySelector('#id_service_type');
        const specificFields = document.querySelectorAll('.service-specific-fields');
        
        if (serviceTypeSelect) {
            function updateFields() {
                // Hide all specific fields first
                specificFields.forEach(field => {
                    field.style.display = 'none';
                });
                
                // Show the selected service type fields
                const selectedType = serviceTypeSelect.value;
                if (selectedType) {
                    const selectedFields = document.getElementById(selectedType + '-fields');
                    if (selectedFields) {
                        selectedFields.style.display = 'block';
                    }
                }
            }
            
            // Initial update
            updateFields();
            
            // Update on change
            serviceTypeSelect.addEventListener('change', updateFields);
        }
    }
    
    // Review Form Handling
    const reviewForm = document.querySelector('.review-form');
    if (reviewForm) {
        const ratingInputs = reviewForm.querySelectorAll('input[name="rating"]');
        const ratingValue = reviewForm.querySelector('.rating-value');
        
        if (ratingInputs.length && ratingValue) {
            ratingInputs.forEach(input => {
                input.addEventListener('change', function() {
                    ratingValue.textContent = this.value;
                });
            });
        }
    }
    
    // Helper function to get CSRF cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Helper function to show toast notifications
    function showToast(message, type = 'success') {
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            // Create toast container if it doesn't exist
            const container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '5';
            document.body.appendChild(container);
            toastContainer = container;
        }
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 3000
        });
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
});