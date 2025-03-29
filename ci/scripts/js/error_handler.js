/**
 * Error handler script for Allure reports
 *
 * Provides error handling functionality for:
 * 1. 401/404 errors in GitHub Pages
 * 2. Missing test results (404 errors for data files)
 * 3. Tab navigation errors (undefined tabs, etc.)
 */
(function() {
    // Run when DOM is loaded
    document.addEventListener('DOMContentLoaded', handleDOMLoaded);

    // Also run immediately for error page detection
    handleErrorPage();

    /**
     * Main entry point - sets up all error handlers
     */
    function handleDOMLoaded() {
        // Set up error handling for missing test data
        interceptFetchRequests();

        // Set up handlers for navigation
        document.addEventListener('click', handleMissingTest, true);
        document.addEventListener('click', handleTabNavigation, true);

        // Fix initial URL hash if needed
        setTimeout(fixInitialUrlHash, 100);
    }

    /**
     * Detect if current page is an error page and redirect
     */
    function handleErrorPage() {
        // Check various indicators of error pages
        const isError = isErrorPage();

        if (isError) {
            console.warn('[Allure Error Handler] Detected error page, redirecting');
            redirectToBase();
        }
    }

    /**
     * Check if current page is an error page (401/404)
     */
    function isErrorPage() {
        const errorIndicators = [
            document.title.includes('401'),
            document.title.includes('404'),
            document.body.innerText.includes('401'),
            document.body.innerText.includes('404'),
            document.body.innerText.includes('Not found'),
            // Check for GitHub Pages specific error messages
            document.body.innerText.includes('File not found'),
            document.body.innerText.includes('Page not found'),
            // Specific page content checks for h1 elements
            document.querySelector('h1')?.innerText === '401',
            document.querySelector('h1')?.innerText === '404'
        ];

        return errorIndicators.some(indicator => indicator);
    }

    /**
     * Redirect to the base URL of the site
     */
    function redirectToBase() {
        // Get current URL parts
        const origin = window.location.origin;
        const pathname = window.location.pathname;
        const repoName = pathname.split('/')[1]; // Get the repository name

        // Try different redirection strategies
        if (repoName) {
            // Strategy 1: Try repository root
            const repoRoot = origin + '/' + repoName;
            console.log('[Allure Error Handler] Redirecting to repository root:', repoRoot);
            window.location.href = repoRoot;
        } else {
            // Strategy 2: Fall back to site root
            console.log('[Allure Error Handler] Redirecting to site root');
            window.location.href = origin;
        }
    }

    /**
     * Intercept fetch requests to handle 404 errors for test results
     */
    function interceptFetchRequests() {
        const originalFetch = window.fetch;

        window.fetch = function(url, options) {
            return originalFetch(url, options).then(function(response) {
                // If request is for a test result and fails with 404
                if (response.status === 404 && url.includes('/data/test-cases/')) {
                    console.warn('[Allure Error Handler] Test result not found:', url);

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
    }

    /**
     * Handle direct navigation to test cases that don't exist
     */
    function handleMissingTest(e) {
        if (e.target.classList.contains('test-case')) {
            const uid = e.target.getAttribute('href').split('/').pop();
            if (!document.querySelector('[data-uid="' + uid + '"]')) {
                e.preventDefault();
                alert('Test result not available. The test may have been removed or renamed in a recent run.');
            }
        }
    }

    /**
     * Handle tab navigation errors (including 'undefined' tab)
     */
    function handleTabNavigation(e) {
        let target = e.target;

        // Ensure we have the link element if click was on a child
        while (target && !target.getAttribute('href') && target.parentElement) {
            target = target.parentElement;
        }

        // Check if this is a tab link
        const href = target.getAttribute('href');
        if (href && href.indexOf('#') === 0) {
            // Special handling for invalid tabs
            if (href === '#undefined' || href === '#null' || href === '#NaN' || href === '') {
                e.preventDefault();
                console.warn('[Allure Error Handler] Invalid tab requested:', href);

                // Find first available tab
                const firstTab = document.querySelector('.allure-tabs a');
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
            const targetTab = document.querySelector(href);
            if (!targetTab) {
                e.preventDefault();
                console.warn('[Allure Error Handler] Tab not found:', href);

                // Find and click first available tab instead
                const firstTab = document.querySelector('.allure-tabs a');
                if (firstTab) {
                    firstTab.click();
                }
            }
        }
    }

    /**
     * Fix direct URL hash navigation on page load
     */
    function fixInitialUrlHash() {
        const hash = location.hash;
        if (hash === '#undefined' || hash === '#null' || hash === '#NaN' || hash === '') {
            // Reset to overview or remove hash
            location.hash = '#overview';
        } else if (hash && !document.querySelector(hash)) {
            // If hash exists but element doesn't, reset to overview
            location.hash = '#overview';
        }
    }
})();
