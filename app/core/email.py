from flask import current_app, render_template
from flask_mail import Mail, Message
from threading import Thread

mail = Mail()

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f'Failed to send email: {str(e)}')

def send_email(subject, sender, recipients, text_body, html_body=None, attachments=None):
    """Send email with optional HTML body and attachments"""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    
    # Send email asynchronously to avoid blocking the request
    Thread(target=send_async_email, 
           args=(current_app._get_current_object(), msg)).start()

def send_contact_email(name, email, subject, message):
    """Send contact form email to admin"""
    admin_email = current_app.config.get('MAIL_USERNAME')
    if not admin_email:
        current_app.logger.error('MAIL_USERNAME not configured')
        return False
    
    try:
        # Email subject
        email_subject = f'[Contact Form] {subject}'
        
        # Email body
        text_body = f"""
Pesan baru dari formulir kontak website:

Nama: {name}
Email: {email}
Subjek: {subject}

Pesan:
{message}

---
Email ini dikirim otomatis dari formulir kontak website.
        """
        
        html_body = f"""
<h3>Pesan baru dari formulir kontak website</h3>
<p><strong>Nama:</strong> {name}</p>
<p><strong>Email:</strong> {email}</p>
<p><strong>Subjek:</strong> {subject}</p>
<p><strong>Pesan:</strong></p>
<div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #007bff; margin: 10px 0;">
    {message.replace(chr(10), '<br>')}
</div>
<hr>
<p><small>Email ini dikirim otomatis dari formulir kontak website.</small></p>
        """
        
        send_email(
            subject=email_subject,
            sender=admin_email,
            recipients=[admin_email],
            text_body=text_body,
            html_body=html_body
        )
        
        return True
        
    except Exception as e:
        current_app.logger.error(f'Failed to send contact email: {str(e)}')
        return False