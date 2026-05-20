document.addEventListener('DOMContentLoaded', () => {
    const sidebarList = document.getElementById('sidebarList');
    if (!sidebarList) {
      console.warn('Sidebar list element not found; skipping sidebar navigation generation.');
      return;
    }
  
    // 1. Add each section_div → h2
    document.querySelectorAll('.section_div').forEach(section => {
      const h2 = section.querySelector('h2');
      if (!h2) return;
      const id    = section.id;
      const title = h2.textContent;
  
      const li = document.createElement('li');
      const a  = document.createElement('a');
      a.href        = `#${id}`;
      a.textContent = title;
  
      li.appendChild(a);
      sidebarList.appendChild(li);
    });
  
    // 2. Add the final Outline header if present
    const outline = document.getElementById('Outline');
    if (outline) {
      const li = document.createElement('li');
      const a  = document.createElement('a');
      a.href        = '#Outline';
      a.textContent = outline.textContent;
      li.appendChild(a);
      sidebarList.appendChild(li);
    }
  
    // 3. Set default side bar width to 20px, fully expand on mouseover
    const sidebar = document.getElementsByClassName('sidebar')[0];
    if (!sidebar) {
      console.warn('Sidebar element not found; skipping sidebar hover behavior.');
      return;
    }
    const sidebarWidth = 220;
    const sidebarMinWidth = 20;
    sidebar.style.width = `${sidebarWidth}px`;

    let collapseTimeout;
    let isHovered = false;

    function scheduleCollapse() {
      clearTimeout(collapseTimeout);
        collapseTimeout = setTimeout(() => {
            if (!isHovered) {
                sidebar.style.width = `${sidebarMinWidth}px`;
            }
        }, 700);
    }

    sidebar.addEventListener('mouseenter', () => {
        isHovered = true;
        sidebar.style.width = `${sidebarWidth}px`;
    });

    sidebar.addEventListener('mouseleave', () => {
        isHovered = false;
        scheduleCollapse();
    });

    // On initial load, schedule collapse if not hovered
    scheduleCollapse();
  });

