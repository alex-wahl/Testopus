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
    
    // Add click handler to test-result links
    document.addEventListener('click', handleMissingTest, true);
});
