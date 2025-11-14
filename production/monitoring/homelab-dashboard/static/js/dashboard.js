// Dashboard JavaScript for enhanced service status checking

// Check service status on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAllServiceStatus();

    // Refresh status every 30 seconds
    setInterval(checkAllServiceStatus, 30000);
});

async function checkAllServiceStatus() {
    const statusIndicators = document.querySelectorAll('.status-indicator');

    // Get all service status from API
    try {
        const response = await fetch('/api/services/health');
        if (response.ok) {
            const healthData = await response.json();

            // Update each service status
            statusIndicators.forEach(async (indicator) => {
                const serviceName = indicator.getAttribute('data-service');
                const healthInfo = healthData.find(h => h.name.toLowerCase() === serviceName);

                if (healthInfo) {
                    updateServiceStatus(indicator, healthInfo.status, healthInfo.message);
                }
            });
        } else {
            // Fallback to individual service checks
            statusIndicators.forEach(async (indicator) => {
                await checkIndividualServiceStatus(indicator);
            });
        }
    } catch (error) {
        console.log('API call failed, checking individual services:', error);
        // Fallback to individual service checks
        statusIndicators.forEach(async (indicator) => {
            await checkIndividualServiceStatus(indicator);
        });
    }
}

async function checkIndividualServiceStatus(indicator) {
    const serviceName = indicator.getAttribute('data-service');

    try {
        const response = await fetch(`/api/services/health/${serviceName}`);
        if (response.ok) {
            const healthInfo = await response.json();
            updateServiceStatus(indicator, healthInfo.status, healthInfo.message);
        } else {
            updateServiceStatus(indicator, 'unknown', 'Unknown');
        }
    } catch (error) {
        updateServiceStatus(indicator, 'unknown', 'Check failed');
    }
}

function updateServiceStatus(indicator, status, message) {
    const dot = indicator.querySelector('.status-dot');
    const text = indicator.querySelector('.status-text');

    // Remove all status classes
    dot.classList.remove('online', 'offline', 'error', 'unknown', 'timeout');

    // Add appropriate status class
    dot.classList.add(status);

    // Update text
    text.textContent = message;
}

// Add smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});
