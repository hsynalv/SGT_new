// Ana JavaScript dosyası

// Sayfa yüklendiğinde çalışacak kodlar
document.addEventListener('DOMContentLoaded', function() {
    // Flash mesajlarını otomatik kapat
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000); // 5 saniye sonra kapat
    });

    // Blog ve duyuru içeriklerindeki resimlere responsive class ekle
    const contentImages = document.querySelectorAll('.blog-content img, .announcement-content img');
    contentImages.forEach(function(img) {
        img.classList.add('img-fluid');
    });

    // Form doğrulama
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Beğeni butonları için AJAX işlemi
    const likeButtons = document.querySelectorAll('.like-button');
    likeButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const url = button.getAttribute('data-url');
            const likeCount = button.querySelector('.like-count');
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    likeCount.textContent = data.likes;
                    button.classList.toggle('liked');
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });

    // Tarih formatını düzenle
    const dateElements = document.querySelectorAll('.format-date');
    dateElements.forEach(function(element) {
        const date = new Date(element.textContent);
        const options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        element.textContent = date.toLocaleDateString('tr-TR', options);
    });
}); 