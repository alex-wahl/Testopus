// Fix date formats to DD-MM-YYYY
document.addEventListener('DOMContentLoaded', function() {
  // Initial fix
  fixDateFormats();
  
  // Also try after dynamic content loads
  setTimeout(fixDateFormats, 1000);
  setTimeout(fixDateFormats, 2000);
  
  function fixDateFormats() {
    // Find all text nodes in the document
    const walker = document.createTreeWalker(
      document.body, 
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    const dateRegex = /(ALLURE\s+REPORT\s+)(\d{1,2})\/(\d{1,2})\/(\d{4})/i;
    let node;
    
    while(node = walker.nextNode()) {
      const matches = node.nodeValue.match(dateRegex);
      if (matches) {
        const [fullMatch, prefix, month, day, year] = matches;
        node.nodeValue = node.nodeValue.replace(
          fullMatch,
          `${prefix}${day}-${month}-${year}`
        );
      }
    }
    
    // Also look for dates in the header
    const headerEls = document.querySelectorAll('header, .header, h1, h2, h3, [class*="header"]');
    headerEls.forEach(el => {
      if (el.innerText && dateRegex.test(el.innerText)) {
        el.innerText = el.innerText.replace(dateRegex, `$1$3-$2-$4`);
      }
    });
  }
}); 