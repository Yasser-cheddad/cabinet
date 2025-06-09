import os
import sys
import argparse
import django
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

load_dotenv()

# Set up Django environment for email functionality
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cabinet.settings')
django.setup()

# Now we can import Django components
from django.core.mail import send_mail

# Configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # Should be a US/Canada number

# Email Configuration
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"

def validate_moroccan_number(phone_number):
    """Validate and format Moroccan phone numbers"""
    # Remove all non-digit characters
    cleaned = ''.join(filter(str.isdigit, phone_number))
    
    # Handle local format (06... or 07...)
    if cleaned.startswith('0') and len(cleaned) == 10:
        return f"+212{cleaned[1:]}"
    
    # Handle international format (+212...)
    if cleaned.startswith('212') and len(cleaned) == 12:
        return f"+{cleaned}"
    
    # Handle already correct format
    if cleaned.startswith('212') and len(cleaned) == 12:
        return f"+{cleaned}"
    
    raise ValueError(f"Invalid Moroccan number format: {phone_number}")

def test_sms_notification(to_phone_number):
    """Test Twilio SMS with better error handling"""
    print("\n=== Testing Twilio SMS ===")
    
    if not to_phone_number:
        to_phone_number = input("Enter a phone number to receive the test SMS (in E.164 format, e.g., +212612345678): ")
    
    try:
        # Validate and format Moroccan numbers
        if to_phone_number.startswith(('+212', '212', '0')):
            to_phone_number = validate_moroccan_number(to_phone_number)
            print(f"Formatted number: {to_phone_number}")

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body="Test message from Medical Cabinet application",
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        
        print(f"✅ SMS sent successfully! SID: {message.sid}")
        return True
    
    except ValueError as e:
        print(f"❌ Number validation error: {str(e)}")
        print("Moroccan numbers must be in format: +2126XXXXXX or 06XXXXXX")
    except TwilioRestException as e:
        print(f"❌ Twilio API error (Code {e.code}): {e.msg}")
        if e.code == 21211:
            print("Solution: Verify the number is in E.164 format and is a valid mobile number")
        elif e.code == 21612:
            print("Solution: Your Twilio number cannot send to Moroccan numbers. Consider:")
            print("- Using a Moroccan Twilio number")
            print("- Requesting international permissions")
            print("- Using WhatsApp instead")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
    
    return False

def test_direct_smtp(to_email):
    """Test email using direct SMTP connection"""
    print("\n=== Testing Direct SMTP Connection ===")
    
    if not to_email:
        to_email = input("Enter an email address to receive the test email: ")
        if not to_email:
            to_email = EMAIL_HOST_USER  # Default to your email for testing
            print(f"Using default email: {to_email}")
    
    # Print email configuration for debugging
    print(f"Email Host: {EMAIL_HOST}")
    print(f"Email Port: {EMAIL_PORT}")
    print(f"Email User: {EMAIL_HOST_USER}")
    print(f"TLS Enabled: {EMAIL_USE_TLS}")
    
    # Create message
    msg = MIMEText("This is a test email sent directly via SMTP from your Medical Cabinet application.")
    msg['Subject'] = 'Direct SMTP Test Email'
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = to_email
    
    try:
        # Connect to server
        print(f"Connecting to {EMAIL_HOST}:{EMAIL_PORT}...")
        if EMAIL_USE_TLS:
            server = smtplib.SMTP(EMAIL_HOST, int(EMAIL_PORT))
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP(EMAIL_HOST, int(EMAIL_PORT))
        
        # Login
        print("Logging in...")
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        
        # Send email
        print("Sending email...")
        server.sendmail(EMAIL_HOST_USER, to_email, msg.as_string())
        print("✅ Email sent successfully via direct SMTP!")
        server.quit()
        return True
    except Exception as e:
        print(f"❌ SMTP Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check if your email provider allows SMTP access")
        print("2. If using Gmail, enable 'Less secure app access' or create an App Password")
        print("3. Verify your email credentials in .env file")
        print("4. Check if your network/firewall allows outgoing connections on port", EMAIL_PORT)
        return False

def test_email_notification(to_email):
    """Test email functionality using Django's send_mail"""
    print("\n=== Testing Email Notification (Django) ===")
    
    if not to_email:
        to_email = input("Enter an email address to receive the test email: ")
        if not to_email:
            to_email = EMAIL_HOST_USER  # Default to your email for testing
            print(f"Using default email: {to_email}")
    
    subject = "Test Email from Medical Cabinet"
    message = "This is a test email from your Medical Cabinet application."
    
    print(f"Sending email to {to_email}...")
    try:
        # Send test email
        send_mail(
            subject=subject,
            message=message,
            from_email=DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False
        )
        
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email failed: {str(e)}")
        print("\nTrying direct SMTP as fallback...")
        return test_direct_smtp(to_email)

def check_twilio_capabilities():
    """Check if account can send to Morocco"""
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        # Try fetching Morocco's pricing - will error if not available
        country = client.pricing.v1.messaging \
                          .countries('MA') \
                          .fetch()
        print("\nTwilio Morocco Capabilities:")
        print(f"Outbound SMS: {'✅ Enabled' if country.outbound_sms_prices else '❌ Disabled'}")
        # Remove the line that tries to access carrier_infos
        # Trial accounts don't have access to this information
        return True
    except TwilioRestException:
        print("❌ Your Twilio account cannot send to Morocco by default")
        print("Visit https://www.twilio.com/console/sms/settings/geo-permissions to enable")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sms', help='Phone number to send test SMS')
    parser.add_argument('--email', help='Email address to send test email')
    parser.add_argument('--direct-smtp', help='Test email using direct SMTP connection')
    parser.add_argument('--check', action='store_true', help='Check Twilio capabilities')
    args = parser.parse_args()

    if args.check:
        check_twilio_capabilities()
    elif args.sms:
        test_sms_notification(args.sms)
    elif args.email:
        test_email_notification(args.email)
    elif args.direct_smtp:
        test_direct_smtp(args.direct_smtp)
    else:
        print("Medical Cabinet Notification Tester")
        print("Options:")
        print("1. Test SMS")
        print("2. Test Email (Django)")
        print("3. Test Email (Direct SMTP)")
        print("4. Check Twilio Morocco Support")
        print("5. Exit")
        
        choice = input("Enter choice (1-5): ")
        if choice == '1':
            test_sms_notification(None)
        elif choice == '2':
            test_email_notification(None)
        elif choice == '3':
            test_direct_smtp(None)
        elif choice == '4':
            check_twilio_capabilities()
        elif choice == '5':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")