/**
 * Admin Dashboard JavaScript
 * Handles admin-specific functionality
 */

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Confirm delete actions
    $('.btn-delete').on('click', function(e) {
        e.preventDefault();
        const itemName = $(this).data('item-name') || 'item ini';
        const deleteUrl = $(this).attr('href') || $(this).closest('form').attr('action');
        
        if (confirm(`Apakah Anda yakin ingin menghapus ${itemName}? Tindakan ini tidak dapat dibatalkan.`)) {
            if ($(this).closest('form').length) {
                $(this).closest('form').submit();
            } else {
                window.location.href = deleteUrl;
            }
        }
    });

    // Auto-refresh dashboard stats every 30 seconds
    if ($('#dashboard-stats').length) {
        setInterval(function() {
            $.get('/admin/api/stats', function(data) {
                $('#total-users').text(data.total_users);
                $('#published-content').text(data.published_content);
                $('#pending-content').text(data.pending_content);
                $('#total-content').text(data.total_content);
            }).fail(function() {
                console.log('Failed to refresh dashboard stats');
            });
        }, 30000);
    }

    // User status toggle
    $('.user-status-toggle').on('change', function() {
        const userId = $(this).data('user-id');
        const isActive = $(this).is(':checked');
        
        $.post('/admin/users/' + userId + '/toggle-status', {
            is_active: isActive
        }).fail(function() {
            alert('Gagal mengubah status user');
            // Revert toggle
            $(this).prop('checked', !isActive);
        });
    });

    // Bulk actions for user management
    $('#select-all-users').on('change', function() {
        $('.user-checkbox').prop('checked', $(this).is(':checked'));
        updateBulkActions();
    });

    $('.user-checkbox').on('change', function() {
        updateBulkActions();
    });

    function updateBulkActions() {
        const checkedCount = $('.user-checkbox:checked').length;
        if (checkedCount > 0) {
            $('#bulk-actions').show();
            $('#bulk-count').text(checkedCount);
        } else {
            $('#bulk-actions').hide();
        }
    }

    // Settings form validation
    $('#settings-form').on('submit', function(e) {
        let isValid = true;
        
        // Validate email
        const email = $('#contact_email').val();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            $('#contact_email').addClass('is-invalid');
            isValid = false;
        } else {
            $('#contact_email').removeClass('is-invalid');
        }

        // Validate phone
        const phone = $('#contact_phone').val();
        if (phone.length < 10) {
            $('#contact_phone').addClass('is-invalid');
            isValid = false;
        } else {
            $('#contact_phone').removeClass('is-invalid');
        }

        if (!isValid) {
            e.preventDefault();
            alert('Mohon periksa kembali form yang Anda isi');
        }
    });

    // Real-time search for users
    $('#user-search').on('keyup', function() {
        const searchTerm = $(this).val().toLowerCase();
        $('.user-row').each(function() {
            const userName = $(this).find('.user-name').text().toLowerCase();
            const userEmail = $(this).find('.user-email').text().toLowerCase();
            
            if (userName.includes(searchTerm) || userEmail.includes(searchTerm)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });

    // Category color picker
    $('#category-color').on('change', function() {
        $(this).css('background-color', $(this).val());
    });

    // Initialize category color
    if ($('#category-color').length) {
        $('#category-color').css('background-color', $('#category-color').val());
    }
});

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

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}