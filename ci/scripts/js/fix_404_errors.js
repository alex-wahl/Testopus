// Fix for 404 errors when test results are missing
document.addEventListener('DOMContentLoaded', function() {
    // Intercept AJAX requests to detect 404 errors for test results
    var originalFetch = window.fetch;
    window.fetch = function(url, options) {
        return originalFetch(url, options).then(function(response) {
            // If request is for a test result and fails with 404
            if (response.status === 404 && url.includes('/data/test-cases/')) {
                console.warn('Test result not found:', url);

                // Create a minimal valid test result to prevent UI errors
                return new Response(JSON.stringify({
                    uid: url.split('/').pop(),
                    name: 'Test result not available',
                    status: 'unknown',
                    time: { start: 0, stop: 0, duration: 0 },
                    statusDetails: {
                        message: 'This test result is no longer available in the report.',
                        trace: 'The test data may have been removed or the ID changed between test runs.'
                    }
                }), {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' }
                });
            }
            return response;
        });
    };

    // Also handle direct navigation to test cases that don't exist
    var handleMissingTest = function(e) {
        if (e.target.classList.contains('test-case')) {
            var uid = e.target.getAttribute('href').split('/').pop();
            if (!document.querySelector('[data-uid="' + uid + '"]')) {
                e.preventDefault();
                alert('Test result not available. The test may have been removed or renamed in a recent run.');
            }
        }
    };

    // Enhanced tab navigation error handling (including 'undefined' tab)
    var handleTabNavigation = function(e) {
        var target = e.target;
        // Ensure we have the link element if click was on a child
        while (target && !target.getAttribute('href') && target.parentElement) {
            target = target.parentElement;
        }

        // Check if this is a tab link
        var href = target.getAttribute('href');
        if (href && href.indexOf('#') === 0) {
            // Special handling for 'undefined' tab and other invalid tabs
            if (href === '#undefined' || href === '#null' || href === '#NaN' || href === '') {
                e.preventDefault();
                console.warn('Invalid tab requested:', href);

                // Find first available tab
                var firstTab = document.querySelector('.allure-tabs a');
                if (firstTab) {
                    firstTab.click();
                    return;
                }

                // If no tabs found, redirect to overview
                if (document.querySelector('[href="#overview"]')) {
                    document.querySelector('[href="#overview"]').click();
                    return;
                }

                // Last resort - reload the page
                location.href = location.href.split('#')[0];
                return;
            }

            // Regular tab that doesn't exist
            var targetTab = document.querySelector(href);
            if (!targetTab) {
                e.preventDefault();
                console.warn('Tab not found:', href);

                // Find and click first available tab instead
                var firstTab = document.querySelector('.allure-tabs a');
                if (firstTab) {
                    firstTab.click();
                }
            }
        }
    };

    // Fix direct URL hash navigation on page load
    var fixInitialUrlHash = function() {
        var hash = location.hash;
        if (hash === '#undefined' || hash === '#null' || hash === '#NaN' || hash === '') {
            // Reset to overview or remove hash
            location.hash = '#overview';
        } else if (hash && !document.querySelector(hash)) {
            // If hash exists but element doesn't, reset to overview
            location.hash = '#overview';
        }
    };

    // Run initial hash fix
    setTimeout(fixInitialUrlHash, 100);

    // Add click handlers
    document.addEventListener('click', handleMissingTest, true);
    document.addEventListener('click', handleTabNavigation, true);
});
