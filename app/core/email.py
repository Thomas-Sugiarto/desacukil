from flask import current_app, render_template
from flask_mail import Mail, Message
from threading import Thread
import logging

mail = Mail()

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info(f'Email sent successfully to {msg.recipients}')
        except Exception as e:
            current_app.logger.error(f'Failed to send email: {str(e)}')
            raise e

def send_email(subject, sender, recipients, text_body, html_body=None, attachments=None):
    """Send email with optional HTML body and attachments"""
    try:
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
        
        return True
    except Exception as e:
        current_app.logger.error(f'Error creating email message: {str(e)}')
        return False

def send_contact_email(name, email, subject, message, phone=None):
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
{f'Telepon: {phone}' if phone else ''}
Subjek: {subject}

Pesan:
{message}

---
Email ini dikirim otomatis dari formulir kontak website.
Untuk membalas, gunakan email: {email}
        """
        
        html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
        📧 Pesan Baru dari Formulir Kontak
    </h2>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <table style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 8px 0; font-weight: bold; color: #34495e; width: 100px;">Nama:</td>
                <td style="padding: 8px 0; color: #2c3e50;">{name}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; font-weight: bold; color: #34495e;">Email:</td>
                <td style="padding: 8px 0;">
                    <a href="mailto:{email}" style="color: #3498db; text-decoration: none;">{email}</a>
                </td>
            </tr>
            {f'<tr><td style="padding: 8px 0; font-weight: bold; color: #34495e;">Telepon:</td><td style="padding: 8px 0; color: #2c3e50;">{phone}</td></tr>' if phone else ''}
            <tr>
                <td style="padding: 8px 0; font-weight: bold; color: #34495e;">Subjek:</td>
                <td style="padding: 8px 0; color: #2c3e50;">{subject}</td>
            </tr>
        </table>
    </div>
    
    <div style="margin: 20px 0;">
        <h3 style="color: #34495e; margin-bottom: 10px;">💬 Pesan:</h3>
        <div style="background-color: #ffffff; padding: 20px; border-left: 4px solid #3498db; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {message.replace(chr(10), '<br>')}
        </div>
    </div>
    
    <div style="margin-top: 30px; padding: 15px; background-color: #ecf0f1; border-radius: 4px; font-size: 12px; color: #7f8c8d;">
        <p style="margin: 0;">
            <strong>📌 Catatan:</strong> Email ini dikirim otomatis dari formulir kontak website.
            <br>Untuk membalas pesan ini, gunakan email: <a href="mailto:{email}" style="color: #3498db;">{email}</a>
        </p>
    </div>
</div>
        """
        
        success = send_email(
            subject=email_subject,
            sender=admin_email,
            recipients=[admin_email],
            text_body=text_body,
            html_body=html_body
        )
        
        if success:
            current_app.logger.info(f'Contact form email sent from {name} ({email})')
        
        return success
        
    except Exception as e:
        current_app.logger.error(f'Failed to send contact email: {str(e)}')
        return False

def send_auto_reply_email(name, email, subject):
    """Send auto-reply email to the person who submitted the contact form"""
    admin_email = current_app.config.get('MAIL_USERNAME')
    if not admin_email:
        return False
    
    try:
        # Auto-reply subject
        reply_subject = f'Re: {subject} - Terima kasih atas pesan Anda'
        
        # Auto-reply body
        text_body = f"""
Halo {name},

Terima kasih telah menghubungi kami melalui website. Kami telah menerima pesan Anda dengan subjek "{subject}".

Tim kami akan segera meninjau pesan Anda dan memberikan respons dalam waktu 1x24 jam pada hari kerja.

Jika ada hal yang mendesak, Anda dapat menghubungi kami langsung melalui:
- Telepon: (informasi dari website)
- Email: {admin_email}

Terima kasih atas kepercayaan Anda.

Salam,
Tim Website Desa
        """
        
        html_body = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 24px;">✉️ Terima Kasih!</h1>
    </div>
    
    <div style="background-color: #ffffff; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <p style="font-size: 16px; color: #2c3e50; margin-bottom: 20px;">
            Halo <strong>{name}</strong>,
        </p>
        
        <p style="color: #34495e; line-height: 1.6;">
            Terima kasih telah menghubungi kami melalui website. Kami telah menerima pesan Anda dengan subjek 
            "<strong style="color: #3498db;">{subject}</strong>".
        </p>
        
        <div style="background-color: #e8f5e8; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #27ae60;">
            <p style="margin: 0; color: #27ae60; font-weight: bold;">
                🕐 Tim kami akan segera meninjau pesan Anda dan memberikan respons dalam waktu <strong>1x24 jam</strong> pada hari kerja.
            </p>
        </div>
        
        <p style="color: #34495e; line-height: 1.6;">
            Jika ada hal yang mendesak, Anda dapat menghubungi kami langsung melalui:
        </p>
        
        <ul style="color: #34495e; line-height: 1.8;">
            <li>📞 Telepon: (sesuai informasi di website)</li>
            <li>📧 Email: <a href="mailto:{admin_email}" style="color: #3498db; text-decoration: none;">{admin_email}</a></li>
        </ul>
        
        <p style="color: #34495e; margin-top: 30px;">
            Terima kasih atas kepercayaan Anda.
        </p>
        
        <p style="color: #34495e; font-weight: bold;">
            Salam,<br>
            Tim Website Desa
        </p>
    </div>
    
    <div style="text-align: center; padding: 20px; color: #7f8c8d; font-size: 12px;">
        <p style="margin: 0;">Email ini dikirim otomatis. Mohon jangan membalas email ini.</p>
    </div>
</div>
        """
        
        success = send_email(
            subject=reply_subject,
            sender=admin_email,
            recipients=[email],
            text_body=text_body,
            html_body=html_body
        )
        
        return success
        
    except Exception as e:
        current_app.logger.error(f'Failed to send auto-reply email: {str(e)}')
        return False