/**
 * Load HTML table files and insert them into the DOM
 */

async function loadTableHTML(htmlPath, containerId) {
    try {
        const response = await fetch(htmlPath);
        if (!response.ok) {
            if (response.status === 404) {
                console.warn(`Skipping missing HTML table resource: ${htmlPath}`);
                const container = document.getElementById(containerId);
                if (container) {
                    container.innerHTML = '<p class="table-warning">Table unavailable (missing source file).</p>';
                }
                return;
            }
            throw new Error(`Failed to load ${htmlPath}: ${response.status}`);
        }
        
        const htmlContent = await response.text();
        const container = document.getElementById(containerId);
        
        if (!container) {
            console.error(`Container with id "${containerId}" not found`);
            return;
        }
        
        container.innerHTML = htmlContent;
        
        // Trigger MathJax to render any LaTeX in the loaded table
        if (window.MathJax && window.MathJax.typesetPromise) {
            await MathJax.typesetPromise([container]);
        }
        
        console.log(`Table loaded successfully into ${containerId}`);
    } catch (error) {
        console.error(`Error loading table from ${htmlPath}:`, error);
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<p class="table-warning">Table unavailable (load error).</p>';
        }
    }
}

async function loadAllHTMLTables() {
    console.log('Loading all tables from HTML files...');
    
    await loadTableHTML('tables/table1_unit_root_tests.html', 'table5-container');
    await loadTableHTML('tables/table2_cointegration_tests.html', 'table6-container');
    await loadTableHTML('tables/table3_neutrality_tests.html', 'table7-container');
    await loadTableHTML('tables/table4_vecm_results.html', 'table8-container');
    
    console.log('All tables loaded successfully');
}

// Make functions available globally
if (typeof window !== 'undefined') {
    window.loadTableHTML = loadTableHTML;
    window.loadAllHTMLTables = loadAllHTMLTables;
}
