// Branch positioning script (v{VERSION})
(function() {
    // Store the actual branch value
    const branchValue = '{BRANCH_NAME}';
    console.log('[Allure Customizer] Branch value: ' + branchValue);
    
    function setBranchName() {
        // Try to directly find and update branch in the DOM
        const envTables = document.querySelectorAll('table');
        let branchUpdated = false;
        
        envTables.forEach(table => {
            // First, remove any existing Branch rows
            const branchRows = Array.from(table.querySelectorAll('tr')).filter(row => {
                const cells = row.querySelectorAll('td');
                return cells.length >= 2 && cells[0].textContent.trim() === 'Branch';
            });
            
            branchRows.forEach(row => row.remove());
            
            // Create new Branch row at the top
            if (table.querySelector('tr')) {
                const firstRow = table.querySelector('tr');
                const newRow = document.createElement('tr');
                newRow.innerHTML = '<td>Branch</td><td>' + branchValue + '</td>';
                
                // Insert before the first row
                firstRow.parentNode.insertBefore(newRow, firstRow);
                branchUpdated = true;
                console.log('[Allure Customizer] Added Branch row to table');
            }
        });
        
        // If we can't find any tables yet, try again later
        if (!branchUpdated && envTables.length === 0) {
            console.log('[Allure Customizer] No tables found, will retry');
            setTimeout(setBranchName, 200);
        }
        
        // Also try to update any JSON/API data in the SPA
        updateAppData();
    }
    
    function updateAppData() {
        try {
            // Check for global app state
            if (window.allureData || window.allure || window.app) {
                const appData = window.allureData || window.allure || window.app;
                
                const findAndUpdateEnv = (obj) => {
                    if (!obj) return;
                    
                    if (Array.isArray(obj)) {
                        // Check if this looks like environment data
                        if (obj.length > 0 && obj[0] && typeof obj[0] === 'object' && 
                            ('name' in obj[0] || 'values' in obj[0])) {
                            
                            // Remove all Branch entries
                            const filteredItems = obj.filter(item => 
                                !(item && typeof item === 'object' && item.name === 'Branch')
                            );
                            
                            // If we need to clean up the array
                            if (filteredItems.length < obj.length) {
                                obj.length = 0; // Clear array
                                filteredItems.forEach(item => obj.push(item)); // Refill with filtered items
                            }
                            
                            // Add Branch at position 0
                            obj.unshift({
                                name: 'Branch',
                                values: [branchValue]
                            });
                            
                            console.log('[Allure Customizer] Updated app data environment');
                        } else {
                            // Recursively check items
                            obj.forEach(item => findAndUpdateEnv(item));
                        }
                    } else if (obj && typeof obj === 'object') {
                        // Check for environment data structure
                        if (obj.environment && Array.isArray(obj.environment)) {
                            // Remove any Branch entries
                            obj.environment = obj.environment.filter(item => 
                                !(item && item.name === 'Branch')
                            );
                            
                            // Add at position 0
                            obj.environment.unshift({
                                name: 'Branch',
                                values: [branchValue]
                            });
                            
                            console.log('[Allure Customizer] Updated app environment array');
                        }
                        
                        // Recursively check all properties
                        Object.values(obj).forEach(val => findAndUpdateEnv(val));
                    }
                };
                
                findAndUpdateEnv(appData);
            }
        } catch (e) {
            console.error('[Allure Customizer] Error updating app data:', e);
        }
    }
    
    // Run immediately 
    setTimeout(setBranchName, 0);
    
    // Run after DOM content loaded
    document.addEventListener('DOMContentLoaded', function() {
        setBranchName();
        // Run several times to catch async renders
        setTimeout(setBranchName, 500);
        setTimeout(setBranchName, 1500);
    });
    
    // Observe DOM changes for SPA navigation
    if ('MutationObserver' in window) {
        const observer = new MutationObserver(function(mutations) {
            // Only update if there are significant DOM changes
            const significantChanges = mutations.some(mutation => 
                mutation.addedNodes.length > 0 && 
                Array.from(mutation.addedNodes).some(node => 
                    node.nodeType === 1 && (
                        node.tagName === 'TABLE' || 
                        node.tagName === 'TR' ||
                        node.querySelector && (
                            node.querySelector('table') ||
                            node.querySelector('tr')
                        )
                    )
                )
            );
            
            if (significantChanges) {
                setBranchName();
            }
        });
        
        // Start observing once DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            console.log('[Allure Customizer] Started DOM observer');
        });
    }
})(); 