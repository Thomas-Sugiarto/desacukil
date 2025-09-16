/**
 * Public Website JavaScript
 * Handles public-facing functionality
 */

$(document).ready(function() {
    // Smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(e) {
        e.preventDefault();
        
        const target = $(this.getAttribute('href'));
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 80
            }, 800);
        }
    });

    // Search functionality
    $('#search-form').on('submit', function(e) {
        const query = $('#search-query').val().trim();
        if (query.length < 2) {
            e.preventDefault();
            alert('Masukkan minimal 2 karakter untuk pencarian');
        }
    });

    // Real-time search suggestions
    let searchTimer;
    $('#search-query').on('input', function() {
        const query = $(this).val().trim();
        
        clearTimeout(searchTimer);
        
        if (query.length >= 2) {
            searchTimer = setTimeout(function() {
                getSearchSuggestions(query);
            }, 300);
        } else {
            $('#search-suggestions').hide();
        }
    });

    // Hide search suggestions when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('#search-container').length) {
            $('#search-suggestions').hide();
        }
    });

    // Contact form validation
    $('#contact-form').on('submit', function(e) {
        let isValid = true;
        
        // Validate name
        const name = $('#name').val().trim();
        if (name.length < 2) {
            $('#name').addClass('is-invalid');
            isValid = false;
        } else {
            $('#name').removeClass('is-invalid');
        }
        
        // Validate email
        const email = $('#email').val().trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            $('#email').addClass('is-invalid');
            isValid = false;
        } else {
            $('#email').removeClass('is-invalid');
        }
        
        // Validate subject
        const subject = $('#subject').val().trim();
        if (subject.length < 5) {
            $('#subject').addClass('is-invalid');
            isValid = false;
        } else {
            $('#subject').removeClass('is-invalid');
        }
        
        // Validate message
        const message = $('#message').val().trim();
        if (message.length < 10) {
            $('#message').addClass('is-invalid');
            isValid = false;
        } else {
            $('#message').removeClass('is-invalid');
        }
        
        if (!isValid) {
            e.preventDefault();
            showNotification('Mohon lengkapi semua field dengan benar', 'error');
        }
    });

    // Lazy loading for images
    if ('IntersectionObserver' in window) {
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

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    // Back to top button
    const backToTop = $('<button id="back-to-top" class="btn btn-primary position-fixed" style="bottom: 20px; right: 20px; z-index: 1000; display: none;"><i class="bi bi-arrow-up"></i></button>');
    $('body').append(backToTop);

    $(window).scroll(function() {
        if ($(this).scrollTop() > 300) {
            $('#back-to-top').fadeIn();
        } else {
            $('#back-to-top').fadeOut();
        }
    });

    $('#back-to-top').on('click', function() {
        $('html, body').animate({scrollTop: 0}, 800);
    });

    // Content sharing
    $('.share-btn').on('click', function(e) {
        e.preventDefault();
        
        const platform = $(this).data('platform');
        const url = encodeURIComponent(window.location.href);
        const title = encodeURIComponent(document.title);
        
        let shareUrl = '';
        
        switch (platform) {
            case 'facebook':
                shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
                break;
            case 'twitter':
                shareUrl = `https://twitter.com/intent/tweet?url=${url}&text=${title}`;
                break;
            case 'whatsapp':
                shareUrl = `https://wa.me/?text=${title} ${url}`;
                break;
            case 'telegram':
                shareUrl = `https://t.me/share/url?url=${url}&text=${title}`;
                break;
        }
        
        if (shareUrl) {
            window.open(shareUrl, '_blank', 'width=600,height=400');
        }
    });

    // Print functionality
    $('.print-btn').on('click', function() {
        window.print();
    });

    // Reading progress indicator
    if ($('.content-detail').length) {
        const progressBar = $('<div id="reading-progress" style="position: fixed; top: 0; left: 0; width: 0%; height: 3px; background: #28a745; z-index: 9999;"></div>');
        $('body').prepend(progressBar);

        $(window).scroll(function() {
            const scrollTop = $(window).scrollTop();
            const docHeight = $(document).height() - $(window).height();
            const scrollPercent = (scrollTop / docHeight) * 100;
            
            $('#reading-progress').css('width', scrollPercent + '%');
        });
    }

    // Newsletter subscription
    $('#newsletter-form').on('submit', function(e) {
        e.preventDefault();
        
        const email = $('#newsletter-email').val().trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!emailRegex.test(email)) {
            showNotification('Email tidak valid', 'error');
            return;
        }
        
        // Simulate newsletter subscription
        showNotification('Terima kasih! Anda telah berlangganan newsletter kami.', 'success');
        $('#newsletter-email').val('');
    });

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Content category filtering
    $('.category-filter').on('click', function(e) {
        e.preventDefault();
        
        const category = $(this).data('category');
        
        $('.category-filter').removeClass('active');
        $(this).addClass('active');
        
        if (category === 'all') {
            $('.content-item').show();
        } else {
            $('.content-item').hide();
            $(`.content-item[data-category="${category}"]`).show();
        }
    });

    // Auto-refresh content list every 5 minutes (for homepage)
    if ($('#content-list').length && window.location.pathname === '/') {
        setInterval(function() {
            $.get('/api/latest-content', function(data) {
                updateContentList(data);
            }).fail(function() {
                console.log('Failed to refresh content');
            });
        }, 300000); // 5 minutes
    }
});

// Search suggestions
function getSearchSuggestions(query) {
    $.get('/api/search-suggestions', {
        q: query
    }).done(function(data) {
        if (data.suggestions && data.suggestions.length > 0) {
            let suggestions = '<ul class="list-group">';
            data.suggestions.forEach(function(suggestion) {
                suggestions += `
                    <li class="list-group-item list-group-item-action">
                        <a href="/content/${suggestion.slug}" class="text-decoration-none">
                            ${suggestion.title}
                        </a>
                    </li>
                `;
            });
            suggestions += '</ul>';
            
            $('#search-suggestions').html(suggestions).show();
        } else {
            $('#search-suggestions').hide();
        }
    });
}

// Content list update
function updateContentList(data) {
    // Update featured content if new content is available
    if (data.latest && data.latest.length > 0) {
        const latestContent = data.latest[0];
        const currentFeatured = $('.featured-content').first();
        
        if (currentFeatured.data('content-id') !== latestContent.id) {
            // Add notification for new content
            showNotification('Konten baru tersedia! Refresh halaman untuk melihat update terbaru.', 'info');
        }
    }
}

// YouTube video lazy loading
function loadYouTubeVideo(container, videoId) {
    const iframe = `
        <iframe width="100%" height="315" 
                src="https://www.youtube.com/embed/${videoId}" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
        </iframe>
    `;
    
    $(container).html(iframe);
}

// Initialize YouTube videos on click
$('.youtube-placeholder').on('click', function() {
    const videoId = $(this).data('video-id');
    loadYouTubeVideo(this, videoId);
});

// Utility functions
function showNotification(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const notification = `
        <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999; max-width: 300px;" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('body').append(notification);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut(function() {
            $(this).remove();
        });
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        timeZone: 'Asia/Jakarta'
    };
    return date.toLocaleDateString('id-ID', options);
}

function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
        return 'Kemarin';
    } else if (diffDays < 7) {
        return `${diffDays} hari yang lalu`;
    } else if (diffDays < 30) {
        const weeks = Math.floor(diffDays / 7);
        return `${weeks} minggu yang lalu`;
    } else {
        return formatDate(dateString);
    }
}