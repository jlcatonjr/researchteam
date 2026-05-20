/**
 * CSV Table Loader
 * Loads CSV files and renders them as HTML tables
 */

function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    const rows = lines.map(line => {
        // Proper CSV parsing that handles quoted fields
        const cells = [];
        let currentCell = '';
        let insideQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            const nextChar = line[i + 1];
            
            if (char === '"') {
                if (insideQuotes && nextChar === '"') {
                    // Escaped quote
                    currentCell += '"';
                    i++; // Skip next quote
                } else {
                    // Toggle quote state
                    insideQuotes = !insideQuotes;
                }
            } else if (char === ',' && !insideQuotes) {
                // End of cell
                cells.push(currentCell.trim());
                currentCell = '';
            } else {
                currentCell += char;
            }
        }
        // Add last cell
        cells.push(currentCell.trim());
        
        return cells;
    });
    return rows;
}

function createTableFromCSV(csvData, tableConfig = {}) {
    const {
        headerRows = 2,
        className = 'results-table',
        hasMultipleSections = false,
        centerAllCells = false  // If true, all cells get center class
    } = tableConfig;
    
    const table = document.createElement('table');
    table.className = className;
    
    let currentSection = null;
    let sectionStartIndex = 0;
    let inHeaderSection = true;
    let headerRowCount = 0;
    
    for (let i = 0; i < csvData.length; i++) {
        const rowData = csvData[i];
        
        // Detect new section starting with "Variable" or similar header patterns
        const isNewSectionStart = (rowData[0] === 'Variable' || rowData[0] !== '' && i > sectionStartIndex + 3) 
                                   && i > sectionStartIndex + 2;
        
        if (isNewSectionStart && hasMultipleSections) {
            // Start new header section
            currentSection = document.createElement('thead');
            table.appendChild(currentSection);
            sectionStartIndex = i;
            inHeaderSection = true;
            headerRowCount = 0;
        } else if (i < headerRows || (inHeaderSection && headerRowCount < headerRows)) {
            // Regular header rows
            if (!currentSection || currentSection.tagName !== 'THEAD') {
                currentSection = document.createElement('thead');
                table.appendChild(currentSection);
            }
            headerRowCount++;
        } else {
            // Body rows
            if (!currentSection || currentSection.tagName !== 'TBODY') {
                currentSection = document.createElement('tbody');
                table.appendChild(currentSection);
                inHeaderSection = false;
            }
        }
        
        const tr = document.createElement('tr');
        const isHeaderRow = currentSection && currentSection.tagName === 'THEAD';
        const cellType = isHeaderRow ? 'th' : 'td';
        
        // Detect rowspan: if current cell has value and next row(s) have empty in same position
        function detectRowspan(rowIdx, colIdx, value) {
            if (value === '') return 1;
            let span = 1;
            let nextRow = rowIdx + 1;
            while (nextRow < csvData.length && csvData[nextRow][colIdx] === '') {
                // Make sure we're still in the same section (not past a header row)
                const nextRowHasContent = csvData[nextRow].some((cell, idx) => idx !== colIdx && cell !== '');
                if (!nextRowHasContent) break; // Hit trailing empty rows
                span++;
                nextRow++;
                // Stop if we hit a new section (check before accessing)
                if (nextRow < csvData.length && csvData[nextRow][0] === 'Variable') break;
            }
            return span;
        }
        
        // Detect colspan: if current cell has value and following cells in same row are empty
        function detectColspan(rowIdx, colIdx, value) {
            if (value === '') return 0; // Empty cells don't render
            let span = 1;
            let nextCol = colIdx + 1;
            while (nextCol < rowData.length && rowData[nextCol] === '') {
                // Check if we've hit trailing empties
                if (rowData.slice(nextCol).every(c => c === '')) break;
                span++;
                nextCol++;
            }
            return span;
        }
        
        // Track which columns we've already rendered (for colspan/rowspan skipping)
        const renderedCols = new Set();
        
        for (let j = 0; j < rowData.length; j++) {
            let cellValue = rowData[j];
            
            // Stop at trailing empty cells
            if (cellValue === '' && rowData.slice(j).every(c => c === '')) {
                break;
            }
            
            // Check if this cell is covered by a previous cell's span
            let isCovered = false;
            
            // Check colspan coverage
            for (let prev = 0; prev < j; prev++) {
                if (rowData[prev] !== '') {
                    const prevColspan = detectColspan(i, prev, rowData[prev]);
                    if (prev + prevColspan > j) {
                        isCovered = true;
                        break;
                    }
                }
            }
            
            // Check rowspan coverage
            if (!isCovered) {
                for (let prevRow = i - 1; prevRow >= 0 && !isCovered; prevRow--) {
                    if (csvData[prevRow] && csvData[prevRow][j] !== '') {
                        const prevRowspan = detectRowspan(prevRow, j, csvData[prevRow][j]);
                        if (prevRow + prevRowspan > i) {
                            isCovered = true;
                            break;
                        } else {
                            // No need to check further back
                            break;
                        }
                    }
                }
            }
            
            if (isCovered) {
                continue; // Skip this cell, it's covered by span
            }
            
            const cell = document.createElement(cellType);
            
            // Detect and apply rowspan (only for non-empty cells)
            if (cellValue !== '') {
                const rowspan = detectRowspan(i, j, cellValue);
                if (rowspan > 1) {
                    cell.setAttribute('rowspan', rowspan);
                }
            }
            
            // Detect and apply colspan (for non-empty cells)
            if (cellValue !== '') {
                const colspan = detectColspan(i, j, cellValue);
                if (colspan > 1) {
                    cell.setAttribute('colspan', colspan);
                }
            }
            
            // Format cell content: add line breaks before parentheses in data cells
            if (!isHeaderRow && cellValue.includes('(') && cellValue.includes(')')) {
                // Match pattern like "-2.439(1)" or "-9.453**(0)" and add <br> before the parenthesis
                cellValue = cellValue.replace(/(\S+)(\(\d+\))/, '$1<br>$2');
            }
            
            cell.innerHTML = cellValue;
            
            // Add center class based on config
            if (centerAllCells || j > 0) {
                cell.className = 'center';
            }
            
            tr.appendChild(cell);
        }
        
        if (currentSection) {
            currentSection.appendChild(tr);
        }
    }
    
    return table;
}

async function loadTableFromCSV(csvPath, containerId, tableConfig = {}) {
    try {
        const response = await fetch(csvPath);
        if (!response.ok) {
            if (response.status === 404) {
                console.warn(`Skipping missing CSV resource: ${csvPath}`);
                const container = document.getElementById(containerId);
                if (container) {
                    container.innerHTML = '<p class="table-warning">Table unavailable (missing source file).</p>';
                }
                return;
            }
            throw new Error(`Failed to load ${csvPath}: ${response.status}`);
        }
        
        const csvText = await response.text();
        const csvData = parseCSV(csvText);
        
        const table = createTableFromCSV(csvData, tableConfig);
        
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '';
            container.appendChild(table);
            
            // Re-render MathJax for the new content
            if (window.MathJax && window.MathJax.typesetPromise) {
                window.MathJax.typesetPromise([container]);
            }
            
            console.log(`Loaded table from ${csvPath} into #${containerId}`);
        } else {
            console.error(`Container #${containerId} not found`);
        }
    } catch (error) {
        console.error(`Error loading table from ${csvPath}:`, error);
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<p class="table-warning">Table unavailable (load error).</p>';
        }
    }
}

// Load all results tables
async function loadAllTables() {
    console.log('Loading all tables from CSV files...');
    
    await loadTableFromCSV('tables/table1_unit_root_tests.csv', 'table5-container', {
        headerRows: 2,
        hasMultipleSections: true
    });
    
    await loadTableFromCSV('tables/table2_cointegration_tests.csv', 'table6-container', {
        headerRows: 1,
        hasMultipleSections: false,
        centerAllCells: true  // All cells in table 2 should be centered
    });
    
    await loadTableFromCSV('tables/table3_neutrality_tests.csv', 'table7-container', {
        headerRows: 1,
        hasMultipleSections: false
    });
    
    await loadTableFromCSV('tables/table4_vecm_results.csv', 'table8-container', {
        headerRows: 2,
        hasMultipleSections: true
    });
    
    console.log('All tables loaded successfully');
}

// Export functions for use in HTML
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { loadTableFromCSV, loadAllTables };
}
