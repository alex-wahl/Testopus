// Date format standardization script (v{VERSION})
document.addEventListener('DOMContentLoaded', function() {
  console.log('[Allure Customizer] Running date format standardization');
  
  // Run immediately and after content might have loaded
  fixAllureDates();
  setTimeout(fixAllureDates, 500);
  setTimeout(fixAllureDates, 1500);
  
  // Also set up a mutation observer to catch dynamic content
  if ('MutationObserver' in window) {
    const observer = new MutationObserver(function(mutations) {
      // Only update if there are textual changes
      const textChanges = mutations.some(mutation => 
        mutation.addedNodes.length > 0 || 
        mutation.type === 'characterData'
      );
      
      if (textChanges) {
        fixAllureDates();
      }
    });
    
    // Start observing the document body for DOM changes
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true
    });
    console.log('[Allure Customizer] Date formatter observer started');
  }
  
  function fixAllureDates() {
    // Convert any MM/DD/YYYY to DD-MM-YYYY in the document
    const datePattern = /(ALLURE REPORT |Allure Report )(\d{1,2})\/(\d{1,2})\/(\d{4})/gi;
    
    // Process all text nodes in the document
    const textNodes = [];
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    let node;
    while (node = walker.nextNode()) {
      if (node.nodeValue.match(datePattern)) {
        node.nodeValue = node.nodeValue.replace(datePattern, function(match, prefix, month, day, year) {
          return prefix + day + '-' + month + '-' + year;
        });
      }
    }
    
    // Also check specific DOM elements that may contain the date
    const headerElements = document.querySelectorAll('.header, [class*="header"], [class*="title"], h1, h2');
    headerElements.forEach(function(el) {
      if (el.innerText && el.innerText.match(datePattern)) {
        el.innerText = el.innerText.replace(datePattern, function(match, prefix, month, day, year) {
          return prefix + day + '-' + month + '-' + year;
        });
      }
    });
  }
}); 