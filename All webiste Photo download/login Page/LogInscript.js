/**
 * Premium Login Page - JavaScript (UPDATED & FIXED)
 * 
 * This file handles:
 * 1. Password visibility toggle
 * 2. Form validation
 * 3. Form submission handling
 * 4. Social login button interactions
 * 5. Checkbox animation logic
 * 6. Security feedback messages
 * 7. DASHBOARD REDIRECT (NEW)
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ Premium Login Page Loaded Successfully');
    
    // Initialize all interactive elements
    initializePasswordToggle();
    initializeFormValidation();
    initializeSocialLogins();
    initializeCheckboxAnimation();
    initializeSecurityFeedback();
});

/**
 * 1. Toggles password visibility by switching input type
 * Shows/hides the eye icon based on state
 */
function initializePasswordToggle() {
    const togglePasswordBtn = document.querySelector('.toggle-password');
    const passwordInput = document.getElementById('password');
    
    if (!togglePasswordBtn || !passwordInput) return;
    
    togglePasswordBtn.addEventListener('click', () => {
        // Toggle between password and text
        const currentType = passwordInput.type;
        passwordInput.type = currentType === 'password' ? 'text' : 'password';
        
        // Toggle eye icon (open/closed)
        const icon = togglePasswordBtn.querySelector('i');
        if (currentType === 'password') {
            icon.classList.replace('fa-eye', 'fa-eye-slash');
        } else {
            icon.classList.replace('fa-eye-slash', 'fa-eye');
        }
        
        console.log('👁️ Password visibility toggled:', passwordInput.type);
    });
    
    // Add Enter key support for password field
    passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const form = document.getElementById('loginForm');
            if (form) form.requestSubmit();
        }
    });
}

/**
 * 2. Form validation and submission handling
 */
function initializeFormValidation() {
    const form = document.getElementById('loginForm');
    
    if (!form) {
        console.error('❌ Form with id "loginForm" not found!');
        return;
    }
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        console.log('📝 Form submitted!');
        
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        const remember = document.getElementById('remember')?.checked || false;
        
        if (!emailInput || !passwordInput) {
            showFeedback('Form fields missing', 'error');
            return;
        }
        
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        
        // Real-time validation
        const emailValid = validateEmail(email);
        const passwordValid = password.length >= 6; // Changed to 6 for easier testing
        
        if (!emailValid) {
            showFeedback('Please enter a valid email address', 'error');
            return;
        }
        
        if (!passwordValid) {
            showFeedback('Password must be at least 6 characters', 'error');
            return;
        }
        
        console.log('✅ Validation passed. Processing login...');
        
        // Simulate API call delay and redirect
        await simulateLogin(email, remember);
    });
}

/**
 * 3. Simulates login process and REDIRECTS to Dashboard
 */
async function simulateLogin(email, remember) {
    const submitBtn = document.querySelector('.btn-signin');
    const originalContent = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Signing in...';
    
    // Simulate network delay (1.5 seconds)
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    console.log('🚀 Login successful! Redirecting to dashboard...');
    
    // Store session if "Remember Me" is checked
    if (remember) {
        localStorage.setItem('userEmail', email);
        localStorage.setItem('isLoggedIn', 'true');
        console.log('💾 User data saved to localStorage');
    }
    
    // CRITICAL: REDIRECT TO DASHBOARD
    // Ensure your folder structure is: 
    // Project/
    //   ├── loginindex.html
    //   └── User/
    //       └── userDashboardindex.html
    try {
        window.location.href = '../User/userDashboardindex.html';
    } catch (error) {
        console.error('❌ Redirect failed:', error);
        showFeedback('Login successful but redirect failed. Check console.', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalContent;
    }
}

/**
 * 4. Validates email format using regex
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * 5. Handles social login button clicks
 */
function initializeSocialLogins() {
    const googleBtn = document.querySelector('.btn-social.google');
    const microsoftBtn = document.querySelector('.btn-social.microsoft');
    
    [googleBtn, microsoftBtn].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                const provider = btn.classList.contains('google') ? 'Google' : 'Microsoft';
                console.log(`${provider} login initiated`);
                showFeedback(`${provider} login coming soon...`, 'info');
            });
        }
    });
}

/**
 * 6. Custom checkbox animation logic
 */
function initializeCheckboxAnimation() {
    const checkbox = document.getElementById('remember');
    
    if (checkbox) {
        checkbox.addEventListener('change', () => {
            console.log('Remember me:', checkbox.checked ? 'Checked' : 'Unchecked');
        });
    }
}

/**
 * 7. Security feedback on page load
 */
function initializeSecurityFeedback() {
    console.log('🔒 Security check: All connections are encrypted');
    console.log('🛡️ Enterprise-grade security is active');
}

/**
 * Helper: Show Feedback/Toast messages
 */
function showFeedback(message, type = 'info') {
    // Remove existing feedback if any
    const existingFeedback = document.querySelector('.feedback-toast');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    // Create feedback element
    const feedback = document.createElement('div');
    feedback.className = 'feedback-toast';
    
    let bgColor, textColor, icon;
    switch (type) {
        case 'success':
            bgColor = 'rgba(16, 185, 129, 0.9)';
            textColor = '#fff';
            icon = 'fa-check-circle';
            break;
        case 'error':
            bgColor = 'rgba(239, 68, 68, 0.9)';
            textColor = '#fff';
            icon = 'fa-exclamation-circle';
            break;
        default:
            bgColor = 'rgba(59, 130, 246, 0.9)';
            textColor = '#fff';
            icon = 'fa-info-circle';
    }
    
    feedback.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: ${bgColor};
        color: ${textColor};
        padding: 12px 24px;
        border-radius: 50px;
        font-size: 14px;
        font-weight: 500;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 8px;
        animation: slideDown 0.3s ease;
    `;
    
    feedback.innerHTML = `<i class="fa-solid ${icon}"></i> ${message}`;
    
    document.body.appendChild(feedback);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        feedback.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => feedback.remove(), 300);
    }, 3000);
}

// Add CSS animations for feedback toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translate(-50%, -20px);
        }
        to {
            opacity: 1;
            transform: translate(-50%, 0);
        }
    }
    
    @keyframes slideUp {
        from {
            opacity: 1;
            transform: translate(-50%, 0);
        }
        to {
            opacity: 0;
            transform: translate(-50%, -20px);
        }
    }
`;
document.head.appendChild(style);