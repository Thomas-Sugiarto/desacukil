/**
 * Publisher Interface JavaScript - FIXED VERSION
 * Handles content creation and editing functionality
 */

$(document).ready(function() {
    // Auto-generate slug from title
    $('#title').on('input', function() {
        const title = $(this).val();
        const slug = generateSlug(title);
        $('#slug-preview').text(slug);
        
        // Check slug availability
        if (slug.length > 0) {
            checkSlugAvailability(slug);
        }
    });

    // Content form validation
    $('#content-form').on('submit', function(e) {
        let isValid = true;
        
        // Validate title
        const title = $('#title').val().trim();
        if (title.length < 5) {
            $('#title').addClass('is-invalid');
            isValid = false;
        } else {
            $('#title').removeClass('is-invalid');
        }
        
        // Validate content
        const content = $('#content').val().trim();
        if (content.length < 10) {
            $('#content').addClass('is-invalid');
            isValid = false;
        } else {
            $('#content').removeClass('is-invalid');
        }
        
        // Validate category
        const category = $('#category_id').val();
        if (!category) {
            $('#category_id').addClass('is-invalid');
            isValid = false;
        } else {
            $('#category_id').removeClass('is-invalid');
        }
        
        if (!isValid) {
            e.preventDefault();
            showNotification('Mohon lengkapi semua field yang wajib diisi', 'error');
        }
    });

    // Auto-save functionality
    let autoSaveTimer;
    $('#content-form input, #content-form textarea').on('input', function() {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(function() {
            autoSaveDraft();
        }, 5000); // Auto-save after 5 seconds of inactivity
    });

    // Character counter for excerpt
    $('#excerpt').on('input', function() {
        const maxLength = 500;
        const currentLength = $(this).val().length;
        const remaining = maxLength - currentLength;
        
        $('#excerpt-counter').text(`${currentLength}/${maxLength} karakter`);
        
        if (remaining < 0) {
            $(this).addClass('is-invalid');
            $('#excerpt-counter').addClass('text-danger');
        } else {
            $(this).removeClass('is-invalid');
            $('#excerpt-counter').removeClass('text-danger');
        }
    });

    // Word counter for content
    $('#content').on('input', function() {
        const wordCount = countWords($(this).val());
        $('#word-counter').text(`${wordCount} kata`);
    });

    // File upload handling
    $('#cover_image').on('change', function() {
        const file = this.files[0];
        if (file) {
            // Validate file size (5MB max)
            if (file.size > 5 * 1024 * 1024) {
                alert('Ukuran file terlalu besar. Maksimal 5MB.');
                $(this).val('');
                $('.image-preview').empty();
                return;
            }
            
            // Validate file type
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
            if (!allowedTypes.includes(file.type)) {
                alert('Tipe file tidak didukung. Gunakan JPG, PNG, WebP, atau GIF.');
                $(this).val('');
                $('.image-preview').empty();
                return;
            }
            
            // Show preview
            const reader = new FileReader();
            reader.onload = function(e) {
                $('.image-preview').html(`
                    <div class="mt-2">
                        <img src="${e.target.result}" class="img-thumbnail" style="max-width: 300px;">
                        <button type="button" class="btn btn-sm btn-danger ms-2 remove-image">
                            <i class="bi bi-trash"></i> Hapus
                        </button>
                    </div>
                `);
            };
            reader.readAsDataURL(file);
        }
    });

    // FIXED: YouTube URL validation and preview
    $('#youtube_url').on('blur input', function() {
        const url = $(this).val().trim();
        if (url) {
            if (isValidYouTubeUrl(url)) {
                $(this).removeClass('is-invalid').addClass('is-valid');
                const videoId = extractYouTubeId(url);
                if (videoId) {
                    showYouTubePreview(videoId);
                }
            } else {
                $(this).addClass('is-invalid').removeClass('is-valid');
                $('.youtube-preview').empty();
            }
        } else {
            $(this).removeClass('is-invalid is-valid');
            $('.youtube-preview').empty();
        }
    });

    // Content status management
    $('.btn-submit-review').on('click', function(e) {
        e.preventDefault();
        
        if (confirm('Apakah Anda yakin ingin mengirim konten ini untuk direview?')) {
            $('#content-form').append('<input type="hidden" name="submit_review" value="1">');
            $('#content-form').submit();
        }
    });

    // Draft management
    $('.btn-save-draft').on('click', function(e) {
        e.preventDefault();
        
        // Add draft flag
        $('#content-form').append('<input type="hidden" name="save_draft" value="1">');
        $('#content-form').submit();
    });

    // Content preview
    $('#preview-btn').on('click', function() {
        showContentPreview();
    });

    // Initialize existing content
    if ($('#content').val()) {
        const wordCount = countWords($('#content').val());
        $('#word-counter').text(`${wordCount} kata`);
    }
    
    if ($('#excerpt').val()) {
        const currentLength = $('#excerpt').val().length;
        $('#excerpt-counter').text(`${currentLength}/500 karakter`);
    }

    // Initialize YouTube preview if URL exists
    const existingYouTubeUrl = $('#youtube_url').val();
    if (existingYouTubeUrl) {
        const videoId = extractYouTubeId(existingYouTubeUrl);
        if (videoId) {
            showYouTubePreview(videoId);
        }
    }

    // Handle remove image button
    $(document).on('click', '.remove-image', function() {
        removeImage();
    });
});

// Slug generation
function generateSlug(title) {
    return title
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
        .replace(/\s+/g, '-') // Replace spaces with hyphens
        .replace(/-+/g, '-') // Replace multiple hyphens with single
        .trim('-'); // Remove leading/trailing hyphens
}

function checkSlugAvailability(slug) {
    const contentId = $('#content-form').data('content-id');
    
    $.get('/publisher/check-slug', {
        slug: slug,
        content_id: contentId
    }).done(function(response) {
        if (response.available) {
            $('#slug-status').html('<i class="bi bi-check-circle text-success"></i> Tersedia');
        } else {
            $('#slug-status').html('<i class="bi bi-x-circle text-danger"></i> Sudah digunakan');
        }
    }).fail(function() {
        $('#slug-status').html('<i class="bi bi-exclamation-circle text-warning"></i> Error checking');
    });
}

// Auto-save functionality
function autoSaveDraft() {
    const formData = new FormData($('#content-form')[0]);
    formData.append('auto_save', 'true');
    
    $.ajax({
        url: $('#content-form').attr('action') || '/publisher/content/auto-save',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function() {
            showAutoSaveIndicator();
        },
        error: function() {
            console.log('Auto-save failed');
        }
    });
}

function showAutoSaveIndicator() {
    $('.save-indicator')
        .text('Draft tersimpan otomatis pada ' + new Date().toLocaleTimeString())
        .removeClass('text-muted')
        .addClass('text-success')
        .fadeIn();
    
    setTimeout(function() {
        $('.save-indicator')
            .removeClass('text-success')
            .addClass('text-muted');
    }, 3000);
}

// Utility functions
function countWords(text) {
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

function removeImage() {
    $('#cover_image').val('');
    $('.image-preview').empty();
}

// FIXED: YouTube URL validation with comprehensive patterns
function isValidYouTubeUrl(url) {
    const patterns = [
        // Standard watch URL: https://www.youtube.com/watch?v=VIDEO_ID
        /^(https?:\/\/)?(www\.)?youtube\.com\/watch\?v=([^&=%\?]{11})/,
        // Short URL: https://youtu.be/VIDEO_ID
        /^(https?:\/\/)?youtu\.be\/([^&=%\?]{11})/,
        // Embed URL: https://www.youtube.com/embed/VIDEO_ID
        /^(https?:\/\/)?(www\.)?youtube\.com\/embed\/([^&=%\?]{11})/,
        // YouTube nocookie: https://www.youtube-nocookie.com/embed/VIDEO_ID
        /^(https?:\/\/)?(www\.)?youtube-nocookie\.com\/embed\/([^&=%\?]{11})/,
        // Mobile URL: https://m.youtube.com/watch?v=VIDEO_ID
        /^(https?:\/\/)?m\.youtube\.com\/watch\?v=([^&=%\?]{11})/,
        // URL with additional parameters
        /^(https?:\/\/)?(www\.)?youtube\.com\/watch\?.*v=([^&=%\?]{11})/
    ];
    
    return patterns.some(pattern => pattern.test(url));
}

// FIXED: YouTube ID extraction with comprehensive patterns
function extractYouTubeId(url) {
    const patterns = [
        // Standard watch URL: https://www.youtube.com/watch?v=VIDEO_ID
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([^&=%\?]{11})/,
        // Short URL: https://youtu.be/VIDEO_ID
        /(?:https?:\/\/)?youtu\.be\/([^&=%\?]{11})/,
        // Embed URL: https://www.youtube.com/embed/VIDEO_ID
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([^&=%\?]{11})/,
        // YouTube nocookie: https://www.youtube-nocookie.com/embed/VIDEO_ID
        /(?:https?:\/\/)?(?:www\.)?youtube-nocookie\.com\/embed\/([^&=%\?]{11})/,
        // Mobile URL: https://m.youtube.com/watch?v=VIDEO_ID
        /(?:https?:\/\/)?m\.youtube\.com\/watch\?v=([^&=%\?]{11})/,
        // URL with additional parameters: https://www.youtube.com/watch?v=VIDEO_ID&t=123s
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?.*v=([^&=%\?]{11})/,
    ];
    
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) {
            return match[1];
        }
    }
    return null;
}

// FIXED: YouTube preview with proper container selection and error handling
function showYouTubePreview(videoId) {
    if (!videoId) {
        console.error('No video ID provided');
        return;
    }

    const preview = `
        <div class="youtube-preview-container mt-3">
            <div class="ratio ratio-16x9" style="max-width: 400px;">
                <iframe src="https://www.youtube.com/embed/${videoId}" 
                        frameborder="0" 
                        allowfullscreen
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        loading="lazy">
                </iframe>
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger mt-2 remove-youtube">
                <i class="bi bi-trash"></i> Hapus Video
            </button>
        </div>
    `;
    
    // Use both class and ID selectors to ensure compatibility
    $('.youtube-preview, #youtube-preview').html(preview);
    
    // Handle remove button
    $(document).on('click', '.remove-youtube', function() {
        removeYouTubePreview();
    });
}

function removeYouTubePreview() {
    $('#youtube_url').val('').removeClass('is-valid is-invalid');
    $('.youtube-preview, #youtube-preview').empty();
}

function showContentPreview() {
    const title = $('#title').val();
    const content = $('#content').val();
    const excerpt = $('#excerpt').val();
    const youtubeUrl = $('#youtube_url').val();
    
    let youtubeEmbed = '';
    if (youtubeUrl) {
        const videoId = extractYouTubeId(youtubeUrl);
        if (videoId) {
            youtubeEmbed = `
                <div class="ratio ratio-16x9 mb-3">
                    <iframe src="https://www.youtube.com/embed/${videoId}" 
                            frameborder="0" allowfullscreen></iframe>
                </div>
            `;
        }
    }
    
    const previewContent = `
        <div class="modal fade" id="contentPreviewModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Preview Konten</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <article>
                            <h1>${title}</h1>
                            ${excerpt ? `<p class="lead">${excerpt}</p>` : ''}
                            ${youtubeEmbed}
                            <div class="content-body">
                                ${content.replace(/\n/g, '<br>')}
                            </div>
                        </article>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Tutup</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    $('#contentPreviewModal').remove();
    
    $('body').append(previewContent);
    $('#contentPreviewModal').modal('show');
    
    // Clean up modal after hiding
    $('#contentPreviewModal').on('hidden.bs.modal', function() {
        $(this).remove();
    });
}

function showNotification(message, type = 'success') {
    const alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
    const notification = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Try multiple notification containers
    const containers = ['#notifications', '.notifications', '.alert-container'];
    let notificationAdded = false;
    
    for (const container of containers) {
        if ($(container).length) {
            $(container).html(notification);
            notificationAdded = true;
            break;
        }
    }
    
    // If no container found, prepend to form
    if (!notificationAdded) {
        $('#content-form').prepend(notification);
    }
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}