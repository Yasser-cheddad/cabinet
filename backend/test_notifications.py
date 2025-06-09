import os
import sys
import django
from django.conf import settings

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cabinet.settings')
django.setup()

from notifications.services import send_sms_notification, send_email_notification

def test_sms():
    """Test SMS functionality using Twilio"""
    print("\n=== Testing SMS Notification ===")
    # You can change this to any valid phone number to receive the test SMS
    to_number = input("Enter phone number to receive test SMS (in E.164 format, e.g., +1234567890): ")
    if not to_number:
        to_number = os.getenv('TWILIO_PHONE_NUMBER')  # Default to your Twilio number for testing
        print(f"Using default number: {to_number}")
    
    message = "This is a test SMS from your Medical Cabinet application."
    
    print(f"Sending SMS to {to_number}...")
    result = send_sms_notification(to_number, message)
    
    if result.get('success'):
        print(f"✅ SMS sent successfully! Message ID: {result.get('message_id')}")
    else:
        print(f"❌ SMS failed: {result.get('error')}")
    
    return result

def test_email():
    """Test email functionality"""
    print("\n=== Testing Email Notification ===")
    # You can change this to any valid email to receive the test email
    to_email = input("Enter email to receive test email: ")
    if not to_email:
        to_email = os.getenv('EMAIL_HOST_USER')  # Default to your email for testing
        print(f"Using default email: {to_email}")
    
    subject = "Test Email from Medical Cabinet"
    message = "This is a test email from your Medical Cabinet application."
    
    print(f"Sending email to {to_email}...")
    result = send_email_notification(to_email, subject, message)
    
    if result:
        print("✅ Email sent successfully!")
    else:
        print("❌ Email failed to send.")
    
    return result

if __name__ == "__main__":
    print("Medical Cabinet Notification Testing Utility")
    print("===========================================")
    
    while True:
        print("\nSelect an option:")
        print("1. Test SMS (Twilio)")
        print("2. Test Email")
        print("3. Test Both")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == "1":
            test_sms()
        elif choice == "2":
            test_email()
        elif choice == "3":
            sms_result = test_sms()
            email_result = test_email()
            
            print("\n=== Summary ===")
            print(f"SMS: {'Success' if sms_result.get('success') else 'Failed'}")
            print(f"Email: {'Success' if email_result else 'Failed'}")
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
