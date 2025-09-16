/**
 * Editor Interface JavaScript
 * Handles content review and editing functionality
 */

$(document).ready(function() {
    // Initialize rich text editor for content editing
    if ($('#content-editor').length) {
        // Simple rich text editor using contenteditable
        $('#content-editor').attr('contenteditable', 'true');
        
        // Add formatting toolbar
        const toolbar = `
            <div class="editor-toolbar mb-2">
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="formatText('bold')">
                    <i class="bi bi-type-bold"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="formatText('italic')">
                    <i class="bi bi-type-italic"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="formatText('underline')">
                    <i class="bi bi-type-underline"></i>
                </button>
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="formatText('insertUnorderedList')">
                        <i class="bi bi-list-ul"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="formatText('insertOrderedList')">
                        <i class="bi bi-list-ol"></i>
                    </button>
                </div>
            </div>
        `;
        $('#content-editor').before(toolbar);
    }

    // Content approval/rejection handling
    $('.btn-approve, .btn-reject').on('click', function(e) {
        e.preventDefault();
        
        const action = $(this).hasClass('btn-approve') ? 'approve' : 'reject';
        const contentId = $(this).data('content-id');
        const contentTitle = $(this).data('content-title') || 'konten ini';
        
        let confirmMessage = action === 'approve' 
            ? `Apakah Anda yakin ingin menyetujui "${contentTitle}"?`
            : `Apakah Anda yakin ingin menolak "${contentTitle}"?`;
        
        if (confirm(confirmMessage)) {
            if (action === 'reject') {
                // Show comment modal for rejection
                showRejectModal(contentId, contentTitle);
            } else {
                // Direct approval
                submitReview(contentId, action, '');
            }
        }
    });

    // Review form submission
    $('#review-form').on('submit', function(e) {
        e.preventDefault();
        
        const action = $('input[name="action"]:checked').val();
        const comment = $('#review_comment').val();
        const contentId = $(this).data('content-id');
        
        if (action === 'reject' && comment.trim() === '') {
            alert('Komentar wajib diisi untuk penolakan konten');
            return;
        }
        
        submitReview(contentId, action, comment);
    });

    // Auto-save draft functionality
    let autoSaveTimer;
    $('#content-form input, #content-form textarea').on('input', function() {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(function() {
            autoSaveDraft();
        }, 3000); // Auto-save after 3 seconds of inactivity
    });

    // Content filtering
    $('#status-filter, #category-filter').on('change', function() {
        filterContent();
    });

    // Real-time content search
    $('#content-search').on('keyup', function() {
        const searchTerm = $(this).val().toLowerCase();
        $('.content-row').each(function() {
            const title = $(this).find('.content-title').text().toLowerCase();
            const author = $(this).find('.content-author').text().toLowerCase();
            
            if (title.includes(searchTerm) || author.includes(searchTerm)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });

    // YouTube URL validation
    $('#youtube_url').on('blur', function() {
        const url = $(this).val();
        if (url && !isValidYouTubeUrl(url)) {
            $(this).addClass('is-invalid');
            $(this).siblings('.invalid-feedback').text('URL YouTube tidak valid');
        } else {
            $(this).removeClass('is-invalid');
            if (url) {
                // Show preview
                const videoId = extractYouTubeId(url);
                if (videoId) {
                    showYouTubePreview(videoId);
                }
            }
        }
    });

    // File upload preview
    $('#cover_image').on('change', function() {
        const file = this.files[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) { // 5MB limit
                alert('Ukuran file terlalu besar. Maksimal 5MB.');
                $(this).val('');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = function(e) {
                $('#image-preview').html(`
                    <img src="${e.target.result}" class="img-thumbnail" style="max-width: 200px;">
                `);
            };
            reader.readAsDataURL(file);
        }
    });
});

// Content review functions
function submitReview(contentId, action, comment) {
    $.post(`/editor/content/${contentId}/review`, {
        action: action,
        review_comment: comment,
        csrf_token: $('meta[name=csrf-token]').attr('content')
    }).done(function(response) {
        showNotification(`Konten berhasil ${action === 'approve' ? 'disetujui' : 'ditolak'}`, 'success');
        setTimeout(function() {
            window.location.href = '/editor/review-queue';
        }, 1500);
    }).fail(function() {
        showNotification('Terjadi kesalahan saat memproses review', 'error');
    });
}

function showRejectModal(contentId, contentTitle) {
    const modal = `
        <div class="modal fade" id="rejectModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Tolak Konten</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Berikan alasan penolakan untuk: <strong>${contentTitle}</strong></p>
                        <textarea class="form-control" id="reject-comment" rows="4" 
                                  placeholder="Masukkan alasan penolakan..." required></textarea>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Batal</button>
                        <button type="button" class="btn btn-danger" onclick="confirmReject(${contentId})">
                            Tolak Konten
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(modal);
    $('#rejectModal').modal('show');
    
    // Clean up modal after hiding
    $('#rejectModal').on('hidden.bs.modal', function() {
        $(this).remove();
    });
}

function confirmReject(contentId) {
    const comment = $('#reject-comment').val().trim();
    if (comment === '') {
        alert('Alasan penolakan harus diisi');
        return;
    }
    
    $('#rejectModal').modal('hide');
    submitReview(contentId, 'reject', comment);
}

// Auto-save functionality
function autoSaveDraft() {
    const formData = new FormData($('#content-form')[0]);
    formData.append('auto_save', 'true');
    
    $.ajax({
        url: $('#content-form').attr('action'),
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function() {
            $('#auto-save-indicator').text('Draft tersimpan otomatis').fadeIn().delay(2000).fadeOut();
        }
    });
}

// Content filtering
function filterContent() {
    const statusFilter = $('#status-filter').val();
    const categoryFilter = $('#category-filter').val();
    
    $('.content-row').each(function() {
        let show = true;
        
        if (statusFilter && $(this).data('status') !== statusFilter) {
            show = false;
        }
        
        if (categoryFilter && $(this).data('category') !== categoryFilter) {
            show = false;
        }
        
        if (show) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
}

// Rich text editor functions
function formatText(command) {
    document.execCommand(command, false, null);
    $('#content-editor').focus();
}

// YouTube helper functions
function isValidYouTubeUrl(url) {
    const regex = /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/(watch\?v=|embed\/|v\/|.+\?v=)?([^&=%\?]{11})/;
    return regex.test(url);
}

function extractYouTubeId(url) {
    const regex = /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/(watch\?v=|embed\/|v\/|.+\?v=)?([^&=%\?]{11})/;
    const match = url.match(regex);
    return match ? match[6] : null;
}

function showYouTubePreview(videoId) {
    const preview = `
        <div class="youtube-preview mt-2">
            <iframe width="300" height="169" src="https://www.youtube.com/embed/${videoId}" 
                    frameborder="0" allowfullscreen></iframe>
        </div>
    `;
    $('#youtube-preview').html(preview);
}

// Utility functions
function showNotification(message, type = 'success') {
    const alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
    const notification = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('#notifications').html(notification);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut();
    }, 5000);
}