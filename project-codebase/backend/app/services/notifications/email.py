import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
from app.core.logging_config import logger

def send_otp_email(to_email: str, otp_code: str):
    """
    Sends a 6-digit OTP code to the user via Gmail SMTP.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP settings not configured. Printing OTP to logs.")
        logger.info(f"OTP for {to_email}: {otp_code}")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL or settings.SMTP_USER}>"
        msg['To'] = to_email
        msg['Subject'] = "Password Reset OTP - Project Nexus"

        body = f"""
        <html>
          <body>
            <h2>Password Reset Request</h2>
            <p>Your One-Time Password (OTP) to reset your password is:</p>
            <h1 style="color: #4A90E2; letter-spacing: 5px;">{otp_code}</h1>
            <p>This code expires in 15 minutes.</p>
            <p>If you did not request this, please ignore this email.</p>
          </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.SMTP_USER, to_email, text)
        server.quit()
        
        logger.info(f"OTP email sent to {to_email}")

    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
        # Log OTP anyway for dev/debug purposes if email fails
        logger.info(f"OTP for {to_email} (fallback): {otp_code}")
