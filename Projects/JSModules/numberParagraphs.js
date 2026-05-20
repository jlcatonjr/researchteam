document.addEventListener('DOMContentLoaded', () => {
	const sections = document.querySelectorAll('.section_div');
	sections.forEach((section, sectionIndex) => {
		const header = section.querySelector('h2');
		// Try extracting section number from header text (e.g., "1." from "1. Something")
		let match = header && header.textContent.match(/^(\d+)\s*\./);
		let sectionNumber = match ? match[1] : (sectionIndex + 1);
		let paraCount = 1;
		// Select all paragraph elements inside this section
		section.querySelectorAll('p').forEach(p => {
			// Skip <p> immediately following a <blockquote>
			if (p.classList.contains('no-number')) return;
			if (p.previousElementSibling && p.previousElementSibling.tagName === 'BLOCKQUOTE') {
				return;
			}
			const numNode = document.createTextNode(`${sectionNumber}.${paraCount} `);
			p.insertBefore(numNode, p.firstChild);
			paraCount++;
		  });
		  
	});
});
