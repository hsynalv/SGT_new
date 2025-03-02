// Siber Güvenlik Temalı JavaScript Dosyası

// Matrix (Kod Yağmuru) Animasyonu için Canvas Oluşturma
function createMatrixAnimation() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // Canvas'ı body'nin en arkasına ekle
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.zIndex = '-2';
    canvas.style.opacity = '0.07';
    canvas.id = 'matrix-canvas';
    
    document.body.prepend(canvas);
    
    // Matrix karakterleri (siber güvenlik ve kodlama sembollerini içerir)
    const characters = '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンABCDEFGHIJKLMNOPQRSTUVWXYZ{}[]<>;:~$#@%&*-+=§±!?';
    
    // Yağmur damlalarının karakterleri ve pozisyonları
    const drops = [];
    // Her bir sütun için bir damla oluştur
    const fontSize = 14;
    const columns = canvas.width / fontSize;
    
    for (let i = 0; i < columns; i++) {
        // Her sütun için rastgele bir Y pozisyonu ile başla
        drops[i] = Math.floor(Math.random() * -canvas.height / fontSize);
    }
    
    // Matrix animasyonunu çiz
    function drawMatrix() {
        // Önceki kareler için hafif bir opaklık ekle (geçmiş karakterleri sil)
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Karakterleri ayarla 
        ctx.fillStyle = '#75a634';
        ctx.font = fontSize + 'px monospace';
        
        // Her sütun için yağmur damlası oluştur
        for (let i = 0; i < drops.length; i++) {
            // Rastgele bir karakter seç
            const text = characters.charAt(Math.floor(Math.random() * characters.length));
            
            // X ve Y koordinatları hesapla
            const x = i * fontSize;
            const y = drops[i] * fontSize;
            
            // Karakteri çiz
            ctx.fillText(text, x, y);
            
            // Y pozisyonunu güncelle
            drops[i]++;
            
            // Eğer yağmur damlası ekranın dışına çıkarsa
            if (y > canvas.height && Math.random() > 0.975) {
                drops[i] = Math.floor(Math.random() * -10); // Yeni bir damla başlat
            }
        }
    }
    
    // Matrix animasyonunu periyodik olarak çağır
    setInterval(drawMatrix, 50);
    
    // Pencere boyutu değiştiğinde canvas'ı yeniden boyutlandır
    window.addEventListener('resize', function() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        // Sütunların sayısını güncelle
        const columns = canvas.width / fontSize;
        
        // Damlaları sıfırla
        for (let i = 0; i < columns; i++) {
            drops[i] = Math.floor(Math.random() * -canvas.height / fontSize);
        }
    });
}

// Siber Güvenlik "Terminal Yazım" Efekti
function typewriterEffect() {
    const elements = document.querySelectorAll('.typewriter');
    
    elements.forEach(element => {
        const text = element.textContent;
        element.textContent = '';
        element.style.borderRight = '0.15em solid #75a634';
        element.style.animation = 'terminal-cursor 0.75s step-end infinite';
        element.style.whiteSpace = 'nowrap';
        element.style.overflow = 'hidden';
        
        let i = 0;
        const speed = 50; // Yazım hızı (ms)
        
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, speed);
            } else {
                // Yazım tamamlandığında cursor animasyonunu kaldır
                setTimeout(() => {
                    element.style.borderRight = 'none';
                    element.style.animation = 'none';
                }, 2000);
            }
        }
        
        type();
    });
}

// Siber Güvenlik "Glitch" Efekti
function addGlitchEffect() {
    const elements = document.querySelectorAll('.glitch-text');
    
    elements.forEach(element => {
        // Orijinal metni sakla
        const originalText = element.textContent;
        let intervalId;
        
        // Mouse üzerine gelindiğinde glitch efektini başlat
        element.addEventListener('mouseenter', () => {
            clearInterval(intervalId);
            
            intervalId = setInterval(() => {
                let glitchedText = '';
                
                // Her karakteri rastgele glitch yapma olasılığı
                for (let i = 0; i < originalText.length; i++) {
                    if (Math.random() < 0.1) {
                        glitchedText += characters.charAt(Math.floor(Math.random() * characters.length));
                    } else {
                        glitchedText += originalText[i];
                    }
                }
                
                element.textContent = glitchedText;
            }, 100);
        });
        
        // Mouse çıktığında orijinal metni geri getir
        element.addEventListener('mouseleave', () => {
            clearInterval(intervalId);
            element.textContent = originalText;
        });
    });
}

// Yükleme Animasyonu
function showLoadingAnimation() {
    // Sayfadaki tüm içeriği gizle
    document.body.style.overflow = 'hidden';
    
    // Yükleme ekranı için div oluştur
    const loadingScreen = document.createElement('div');
    loadingScreen.className = 'loading-screen';
    
    // Animasyon içeriği
    loadingScreen.innerHTML = `
        <div class="loading-animation">
            <div class="loading-spinner"></div>
            <div class="loading-text">Güvenli bağlantı kuruluyor...</div>
        </div>
    `;
    
    // Body'nin başına ekle
    document.body.prepend(loadingScreen);
    
    // 2 saniye sonra yükleme ekranını kaldır
    setTimeout(() => {
        loadingScreen.classList.add('fade-out');
        setTimeout(() => {
            loadingScreen.remove();
            document.body.style.overflow = 'auto';
        }, 500);
    }, 2000);
}

// Terminal UI Oluşturma
function createTerminalElement(title, commands) {
    const terminal = document.createElement('div');
    terminal.className = 'terminal-window';
    
    // Terminal başlığı ve butonları
    const header = document.createElement('div');
    header.className = 'terminal-header';
    header.innerHTML = `
        <div class="terminal-title">${title}</div>
        <div class="terminal-buttons">
            <div class="terminal-button terminal-button-red"></div>
            <div class="terminal-button terminal-button-yellow"></div>
            <div class="terminal-button terminal-button-green"></div>
        </div>
    `;
    
    terminal.appendChild(header);
    
    // Terminal içeriği
    const content = document.createElement('div');
    content.className = 'terminal-content';
    
    // Terminal komutları
    commands.forEach(cmd => {
        // Her bir komut için prompt ve komut satırı oluştur
        const promptLine = document.createElement('div');
        promptLine.className = 'terminal-prompt';
        promptLine.innerHTML = `<span class="terminal-command">${cmd.command}</span>`;
        content.appendChild(promptLine);
        
        // Eğer bir çıktı varsa göster
        if (cmd.output) {
            const outputLine = document.createElement('div');
            outputLine.className = 'terminal-output';
            outputLine.textContent = cmd.output;
            content.appendChild(outputLine);
        }
    });
    
    terminal.appendChild(content);
    
    return terminal;
}

// Cyber Badges Oluşturma
function createCyberBadges() {
    const badges = document.querySelectorAll('.badge');
    
    badges.forEach(badge => {
        if (!badge.classList.contains('cyber-badge') && !badge.closest('.navbar')) {
            // Orijinal içeriği ve sınıfları koru
            const content = badge.innerHTML;
            const isBgSuccess = badge.classList.contains('bg-success');
            const isBgDanger = badge.classList.contains('bg-danger');
            const isBgInfo = badge.classList.contains('bg-info');
            const isBgWarning = badge.classList.contains('bg-warning');
            
            // Eski sınıf isimlerini kaldır ve cyber-badge ekle
            badge.className = '';
            badge.classList.add('cyber-badge');
            
            // Orijinal içeriği geri ekle
            badge.innerHTML = content;
            
            // Orijinal renk sınıfına göre özel stil ekle
            if (isBgSuccess) badge.style.color = '#2ecc40';
            if (isBgDanger) badge.style.color = '#ff4136';
            if (isBgInfo) badge.style.color = '#39cccc';
            if (isBgWarning) badge.style.color = '#ffdc00';
        }
    });
}

// Sayfa yüklendiğinde çalışacak kodlar
document.addEventListener('DOMContentLoaded', function() {
    // Siber güvenlik animasyonları
    createMatrixAnimation();
    typewriterEffect();
    addGlitchEffect();
    
    // Yükleme animasyonunu sadece ana sayfada ve ilk ziyarette göster
    const isHomePage = window.location.pathname === '/' || 
                        window.location.pathname === '/index' || 
                        window.location.pathname === '/index.html';
    
    const hasVisitedBefore = sessionStorage.getItem('visited');
    
    if (isHomePage && !hasVisitedBefore) {
        showLoadingAnimation();
        // Ziyareti kaydet
        sessionStorage.setItem('visited', 'true');
    }
    
    // Siber güvenlik UI öğelerini oluştur
    createCyberBadges();
    
    // Ana sayfa için terminal örneği ekle
    if (document.querySelector('.jumbotron') || document.querySelector('.hero-section')) {
        const mainContent = document.querySelector('.jumbotron') || document.querySelector('.hero-section');
        
        // Örnek terminal komutu
        const securityCommands = [
            { command: 'nmap -sS -sV -O targethost', output: 'Starting Nmap scan...' },
            { command: 'sudo tcpdump -i eth0 port 80', output: 'Capturing network traffic...' },
            { command: 'hashcat -m 0 -a 0 hash.txt wordlist.txt', output: 'Session initialized...' }
        ];
        
        const terminal = createTerminalElement('Siber Güvenlik Terminali', securityCommands);
        
        // Terminal öğesini içerik sonrasına ekle
        if (mainContent.nextElementSibling) {
            mainContent.parentNode.insertBefore(terminal, mainContent.nextElementSibling);
        } else {
            mainContent.parentNode.appendChild(terminal);
        }
    }
    
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
    
    // H1 ve H2 başlıklarına siber güvenlik efekti ekle
    const headings = document.querySelectorAll('h1:not(.navbar-brand), h2:not(.card-title)');
    headings.forEach(heading => {
        heading.classList.add('glitch-text');
    });
    
    // Card başlıklarına typewriter efekti ekle
    const cardTitles = document.querySelectorAll('.card-title');
    cardTitles.forEach(title => {
        if (Math.random() > 0.5) { // Rastgele bazı başlıklara uygula
            title.classList.add('typewriter');
        }
    });
}); 