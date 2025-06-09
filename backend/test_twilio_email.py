import os
import django
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path)

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cabinet.settings')
django.setup()

# Test functions
def test_twilio():
    """Test Twilio SMS functionality"""
    from twilio.rest import Client
    
    # Get credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    # Test phone number (using the same Twilio number for testing)
    to_number = from_number
    
    print(f"Twilio Account SID: {account_sid[:5]}...{account_sid[-5:]}")
    print(f"Twilio Auth Token: {auth_token[:5]}...{auth_token[-5:]}")
    print(f"Twilio Phone Number: {from_number}")
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Send test message
        message = client.messages.create(
            body="Test message from Medical Cabinet application",
            from_=from_number,
            to=to_number
        )
        
        print(f"✅ SMS sent successfully! Message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"❌ SMS failed: {str(e)}")
        return False

def test_email():
    """Test email functionality"""
    from django.core.mail import send_mail
    
    # Get email settings
    from_email = os.getenv('DEFAULT_FROM_EMAIL')
    to_email = os.getenv('EMAIL_HOST_USER')  # Send to yourself for testing
    
    print(f"From Email: {from_email}")
    print(f"To Email: {to_email}")
    print(f"Email Host: {os.getenv('EMAIL_HOST')}")
    print(f"Email Port: {os.getenv('EMAIL_PORT')}")
    
    try:
        # Send test email
        send_mail(
            subject="Test Email from Medical Cabinet",
            message="This is a test email from your Medical Cabinet application.",
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False
        )
        
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Medical Cabinet Notification Test")
    print("================================")
    
    print("\n--- Testing Twilio SMS ---")
    twilio_result = test_twilio()
    
    print("\n--- Testing Email ---")
    email_result = test_email()
    
    print("\n--- Test Summary ---")
    print(f"Twilio SMS: {'✅ Success' if twilio_result else '❌ Failed'}")
    print(f"Email: {'✅ Success' if email_result else '❌ Failed'}")
