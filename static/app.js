/**
 * VocabPro - Main JavaScript
 * Handles all frontend functionality
 */

// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
});

// Smooth Scroll for Anchor Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Form Input Sanitization
document.querySelectorAll('input[type="text"], input[type="email"]').forEach(input => {
    input.addEventListener('input', function() {
        // Trim whitespace
        if (this.type !== 'tel') {
            this.value = this.value.trim();
        }
    });
});

// Prevent form resubmission on refresh
if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.href);
}

// Add loading state to all forms
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        const submitBtn = this.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
            submitBtn.classList.add('opacity-75', 'cursor-not-allowed');
        }
    });
});

// Console branding
console.log('%c VocabPro ', 'background: #2196F3; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;');
console.log('Learn English daily via WhatsApp!');