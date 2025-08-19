// Funcionalidad del menú hamburguesa
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');
    const body = document.body;

    //Menu se despliega al ahcer click en hamburguesa
    hamburger.addEventListener('click', function () {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
        body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
    });

    

    //Sub menu se despliega al hacer click en los menu
    document.querySelectorAll('.has-submenu > a').forEach(link => {
        link.addEventListener('click', function(e) {
          e.preventDefault(); // Evita que salte al top
      
          const parentLi = this.parentElement;
          parentLi.classList.toggle('open');      
          
        });
    });

    // Cerrar menú si se hace clic fuera del nav-menu y hamburguesa
    document.addEventListener('click', function (e) {
        const isClickInsideMenu = navMenu.contains(e.target);
        const isClickOnHamburger = hamburger.contains(e.target);

        if (!isClickInsideMenu && !isClickOnHamburger && navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            hamburger.classList.remove('active');
            body.style.overflow = '';

            // Cerrar todos los submenús abiertos
            document.querySelectorAll('.has-submenu.open').forEach(item => {
                item.classList.remove('open');
            });
        }

        
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            hamburger.classList.remove('active');
            body.style.overflow = '';
        }

        // Cerrar todos los submenús abiertos
        document.querySelectorAll('.has-submenu.open').forEach(item => {
            item.classList.remove('open');
        });
    });
    

   

    // Scroll suave para enlaces internos
    const smoothScrollLinks = document.querySelectorAll('a[href^="#"]');
    smoothScrollLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                const headerHeight = document.querySelector('.header').offsetHeight;
                const targetPosition = targetSection.offsetTop - headerHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Header con efecto de scroll
    const header = document.querySelector('.header');
    let lastScrollTop = 0;

    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Agregar sombra al header cuando se hace scroll
        if (scrollTop > 50) {
            header.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
        } else {
            header.style.boxShadow = 'none';
        }
        
        //lastScrollTop = scrollTop;
    });

    // Animaciones al hacer scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observar elementos para animaciones
    const animatedElements = document.querySelectorAll('.agenda-card, .event-card, .contact-item');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    // Validación del formulario de contacto
    const contactForm = document.querySelector('#contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;

            submitBtn.textContent = 'Enviando...';
            submitBtn.disabled = true;

            fetch('/enviar-contacto', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert('¡Gracias por tu mensaje! Te contactaremos pronto.');
                    this.reset();
                } else {
                    alert('Hubo un problema al enviar tu mensaje.');
                }
            })
            .catch(err => {
                console.error(err);
                alert('Error al enviar el mensaje.');
            })
            .finally(() => {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            });
        });
    }

    // Efecto parallax suave en el hero
    const hero = document.querySelector('.hero');
    if (hero) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            hero.style.transform = `translateY(${rate}px)`;
        });
    }

    // Contador de eventos (ejemplo)
    function updateEventCountdown() {
        const eventCards = document.querySelectorAll('.event-card');
        const currentDate = new Date(); // Obtener la fecha actual una sola vez
    
        eventCards.forEach(card => {
            // Obtener la fecha completa del evento desde el atributo de datos
            const eventDateString = card.dataset.fechaEvento;
            if (!eventDateString) {
                return; // Si no hay fecha, saltar al siguiente evento
            }
    
            // Crear un objeto Date para la fecha del evento
            const eventDate = new Date(eventDateString);
    
            // Calcular la diferencia en milisegundos y luego convertir a días
            const timeDifference = eventDate.getTime() - currentDate.getTime();
            const daysUntil = Math.ceil(timeDifference / (1000 * 60 * 60 * 24));
    
            // Crear solo si no existe
            const existing = card.querySelector('.countdown');
            if (!existing && daysUntil >= 0) { // Solo si falta 0 o más días
                const countdown = document.createElement('div');
                countdown.className = 'countdown';
                countdown.style.cssText = `
                    position: absolute;
                    top: 0px;
                    right: 0px;
                    color: white;
                    padding: 5px 10px;
                    border-radius: 5px 14px 5px 20px;
                    font-size: 0.8rem;
                    font-weight: 600;
                `;
    
                if (daysUntil === 0) {
                    countdown.textContent = "Hoy";
                    countdown.style.background = "#2bb38a"; // verde
                } else if (daysUntil === 1) {
                    countdown.textContent = "1 día";
                    countdown.style.background = "#e74c3c"; // rojo
                } else if (daysUntil > 1) {
                    countdown.textContent = `${daysUntil} días`;
                    countdown.style.background = "#e74c3c"; // rojo
                }
                
                card.style.position = 'relative';
                card.appendChild(countdown);
            }
        });
    }

    // Actualizar contador cada día
    updateEventCountdown();
    setInterval(updateEventCountdown, 86400000); // 24 horas

    // Efecto de hover en las tarjetas de agenda
    const agendaCards = document.querySelectorAll('.agenda-card');
    agendaCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Lazy loading para imágenes (cuando se agreguen)
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));

    // Botón de "volver arriba"
    const backToTopBtn = document.createElement('button');
    backToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopBtn.className = 'back-to-top';
    backToTopBtn.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #4a7c59, #6b8e6b);
        color: white;
        border: none;
        border-radius: 50%;
        cursor: pointer;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        z-index: 1000;
        box-shadow: 0 5px 15px rgba(74, 124, 89, 0.3);
    `;
    
    document.body.appendChild(backToTopBtn);

    // Mostrar/ocultar botón de volver arriba
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.opacity = '1';
            backToTopBtn.style.visibility = 'visible';
        } else {
            backToTopBtn.style.opacity = '0';
            backToTopBtn.style.visibility = 'hidden';
        }
    });

    // Funcionalidad del botón volver arriba
    backToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Efecto de hover en el botón
    backToTopBtn.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-3px)';
        this.style.boxShadow = '0 8px 25px rgba(74, 124, 89, 0.4)';
    });

    backToTopBtn.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
        this.style.boxShadow = '0 5px 15px rgba(74, 124, 89, 0.3)';
    });

    const readMoreBtn = document.getElementById('readMoreBtn');
    if (readMoreBtn) {
        readMoreBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const moreText = document.getElementById('more');
            const dots = document.getElementById('dots');
            if (moreText.style.display === 'none') {
                moreText.style.display = 'inline';
                dots.style.display = 'none';
                readMoreBtn.textContent = 'Leer menos';
            } else {
                moreText.style.display = 'none';
                dots.style.display = 'inline';
                readMoreBtn.textContent = 'Leer más...';
            }
        });
    }
}); 

// Chequeo de sesión iniciada
async function checkUser() {
    try {
        const res = await fetch('/users/me', { credentials: 'include' });
        if (res.ok) {
            const user = await res.json();

            // Desktop
            document.getElementById('login-link').style.display = 'none';
            document.getElementById('user-info').style.display = '';
            document.getElementById('user-email').textContent = user.email;

            // Mobile
            document.getElementById('user-icon').style.display = 'none';
            document.getElementById('login-link-mobile').style.display = 'none';
            document.getElementById('user-email-mobile').textContent = user.email;

            const adminLink = document.getElementById('admin-link');
            const adminLinkMobile = document.getElementById('admin-link-mobile');
            if (user.is_superuser) {
                if (adminLink) adminLink.style.display = '';
                if (adminLinkMobile) adminLinkMobile.style.display = 'block';
            }

            // Logout mobile
            const logoutBtnMobile = document.getElementById('logout-btn-mobile');
            if (logoutBtnMobile) {
                logoutBtnMobile.addEventListener('click', async function () {
                    await fetch('/auth/jwt/logout', { method: 'POST', credentials: 'include' });
                    window.location.reload();
                });
            }

        } else {
            document.getElementById('login-link').style.display = '';
            document.getElementById('user-info').style.display = 'none';
            document.getElementById('user-icon').style.display = 'none';
            document.getElementById('logout-btn-mobile').style.display = 'none';
        }
    } catch (e) {
        document.getElementById('login-link').style.display = '';
        document.getElementById('user-info').style.display = 'none';
        document.getElementById('user-icon').style.display = 'none';
    }
}

// Logout para desktop
document.addEventListener('DOMContentLoaded', function () {
    checkUser();

    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function () {
            await fetch('/auth/jwt/logout', { method: 'POST', credentials: 'include' });
            window.location.reload();
        });
    }

    // Toggle menú móvil al tocar el ícono de perfil
    const userIcon = document.getElementById("user-icon");
    const userDropdown = document.getElementById("user-dropdown");

    if (userIcon && userDropdown) {
        userIcon.addEventListener("click", function (e) {
            e.stopPropagation(); // evita cerrar inmediatamente
            userDropdown.style.display = userDropdown.style.display === "block" ? "none" : "block";
        });

        // Cerrar si se hace clic fuera
        document.addEventListener("click", function (e) {
            if (!userIcon.contains(e.target)) {
                userDropdown.style.display = "none";
            }
        });
    }
});