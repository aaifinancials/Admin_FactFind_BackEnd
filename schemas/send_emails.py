from email.message import EmailMessage
from dotenv import find_dotenv, load_dotenv
import os
import smtplib
from email.mime.text import MIMEText

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

email_address = os.getenv("email_address")
email_password = os.getenv("email_password")


RESET_TOKEN_EXPIRE_MINUTES = 60


async def send_verification_email(to_email: str, code: str):
    subject = "Verify your email"
    body = f"Your verification code is: {code}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email_address
    msg["To"] = to_email

    smtp_server = "smtp.hostinger.com"
    smtp_port = 465

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(email_address, email_password)
            server.send_message(msg)
            print('sent')
    except Exception as e:
        print(f"Email send failed: {e}")


def send_email(to_email: str, reset_link: str):
    """
    Send the password reset link via email.
    """
    msg = EmailMessage()

    message = f"""
Hello,

You requested to reset your password. Click the link below to reset it:
{reset_link}

This link will expire in {RESET_TOKEN_EXPIRE_MINUTES} minutes.

If you did not request a password reset, please ignore this email.

Best regards,
AAI Financials
www.aaifinancials.com
"""

    msg["Subject"] = "Reset Your Password"
    msg["From"] = email_address
    msg["To"] = to_email
    msg.set_content(message)
    
    with smtplib.SMTP_SSL("smtp.hostinger.com", 465) as smtp:
        smtp.login(email_address, email_password)
        smtp.send_message(msg)

def send_referral_email(to_email: str, referrer_email: str, referral_id: str):
    """
    Send referral email to the referred person.
    """
    msg = EmailMessage()

    registration_link = "https://aaifinancials.com/app/customer/sign-up"

    message = f"""
Hello,

You have been referred by {referrer_email}.
Referral ID: {referral_id}

Click the link below to register as a customer:
{registration_link}

Best regards,
AAI Financials
www.aaifinancials.com
"""

    msg["Subject"] = "You've been referred!"
    msg["From"] = email_address
    msg["To"] = to_email
    msg.set_content(message)
    print(msg)

    try:
        with smtplib.SMTP_SSL("smtp.hostinger.com", 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        print("Referral email sent successfully")
    except Exception as e:
        print(f"Failed to send referral email: {e}")
