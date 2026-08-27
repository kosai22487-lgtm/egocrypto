// Precise customer service click handler
document.addEventListener('DOMContentLoaded', function() {
    const allElements = document.querySelectorAll('*');
    allElements.forEach(el => {
        if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE') return;
        // Check if element has exactly one text node child with text 'customer service'
        if (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3 && el.childNodes[0].textContent.trim() === 'customer service') {
            el.style.cursor = 'pointer';
            el.addEventListener('click', function(e) {
                e.preventDefault();
                fetch('/api/get-settings')
                .then(r => r.json())
                .then(data => {
                    if (data.telegram_link) {
                        window.open(data.telegram_link, '_blank');
                    }
                });
            });
        }
    });
});
