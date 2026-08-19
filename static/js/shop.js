document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
        const query = this.value.toLowerCase().trim();
        const productCards = document.querySelectorAll('.product-card');

        productCards.forEach(card => {
            const container = card.closest('.col-lg-4') || card.parentElement;
            const title = card.querySelector('h3')?.textContent.toLowerCase() || '';
            const description = card.querySelector('.description')?.textContent.toLowerCase() || '';

            if (title.includes(query) || description.includes(query)) {
                container.style.display = '';
            } else {
                container.style.display = 'none';
            }
        });
    });
});
