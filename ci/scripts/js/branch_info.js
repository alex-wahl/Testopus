// Fix for branch tab and 404 errors
document.addEventListener('DOMContentLoaded', function() {
    // Add branch data attribute to body
    document.body.setAttribute('data-branch', '{{BRANCH_NAME}}');
    
    // Fix 404 errors on tab navigation
    var handleAnchorClick = function(e) {
        var href = e.target.getAttribute('href');
        if (href && href.indexOf('#') === 0) {
            var targetTab = document.querySelector(href);
            if (!targetTab) {
                e.preventDefault();
                console.warn('Tab not found:', href);
                // Redirect to first available tab instead
                var firstTab = document.querySelector('.allure-tabs a');
                if (firstTab) firstTab.click();
            }
        }
    };
    
    // Add listeners to tab navigation links
    var tabLinks = document.querySelectorAll('.allure-tabs a');
    tabLinks.forEach(function(link) {
        link.addEventListener('click', handleAnchorClick);
    });
});
