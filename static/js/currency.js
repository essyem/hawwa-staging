/**
 * Currency formatting functions for QAR
 */

// Currency configuration
const CURRENCY_CONFIG = {
    symbol: 'QAR',
    code: 'QAR',
    position: 'before', // 'before' or 'after'
    decimalPlaces: 2,
    thousandSeparator: ',',
    decimalSeparator: '.'
};

/**
 * Format a number as QAR currency
 * @param {number|string} amount - The amount to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount, decimals = 2) {
    if (amount === null || amount === undefined || amount === '') {
        amount = 0;
    }
    
    const num = parseFloat(amount);
    if (isNaN(num)) {
        return `QAR 0.00`;
    }
    
    const formatted = num.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
    
    if (CURRENCY_CONFIG.position === 'before') {
        return `${CURRENCY_CONFIG.symbol} ${formatted}`;
    } else {
        return `${formatted} ${CURRENCY_CONFIG.symbol}`;
    }
}

/**
 * Format currency without decimal places for large amounts
 * @param {number|string} amount - The amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrencyShort(amount) {
    return formatCurrency(amount, 0);
}

/**
 * Get currency symbol
 * @returns {string} Currency symbol
 */
function getCurrencySymbol() {
    return CURRENCY_CONFIG.symbol;
}

/**
 * Get currency code
 * @returns {string} Currency code
 */
function getCurrencyCode() {
    return CURRENCY_CONFIG.code;
}

/**
 * Update all elements with data-currency attribute
 */
function updateCurrencyElements() {
    document.querySelectorAll('[data-currency]').forEach(element => {
        const amount = element.getAttribute('data-currency');
        const decimals = element.getAttribute('data-decimals') || 2;
        element.textContent = formatCurrency(amount, parseInt(decimals));
    });
}

/**
 * Replace all $ symbols with QAR in text content
 * @param {string} text - Text to process
 * @returns {string} Processed text
 */
function replaceDollarWithQAR(text) {
    return text.replace(/\$\s*(\d[\d,]*\.?\d*)/g, (match, amount) => {
        return formatCurrency(amount.replace(/,/g, ''));
    });
}

// Auto-update currency elements when DOM is loaded
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', updateCurrencyElements);
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatCurrency,
        formatCurrencyShort,
        getCurrencySymbol,
        getCurrencyCode,
        updateCurrencyElements,
        replaceDollarWithQAR,
        CURRENCY_CONFIG
    };
}
