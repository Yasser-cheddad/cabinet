import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client

# Twilio credentials
TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN = ""
TWILIO_PHONE_NUMBER = ""

# Email credentials
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "cheddadyasse2002@gmail.com"
EMAIL_HOST_PASSWORD = ""

def test_twilio():
    """Test Twilio SMS functionality"""
    print("\n=== Testing Twilio SMS ===")
    
    # Get a phone number to send the test SMS to
    to_number = input("Enter a phone number to receive the test SMS (in E.164 format, e.g., +1234567890): ")
    if not to_number or to_number == TWILIO_PHONE_NUMBER:
        print("⚠️ Warning: You must enter a different phone number than your Twilio number.")
        print("   Twilio doesn't allow sending from a number to itself.")
        return False
    
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send test message
        message = client.messages.create(
            body="Test message from Medical Cabinet application",
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        
        print(f"✅ SMS sent successfully! Message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"❌ SMS failed: {str(e)}")
        return False

def test_email():
    """Test email functionality using SMTP directly"""
    print("\n=== Testing Email ===")
    
    # Get an email to send the test to
    to_email = input("Enter an email address to receive the test email: ")
    if not to_email:
        to_email = EMAIL_HOST_USER  # Default to your own email
    
    try:
        # Create SMTP connection
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.ehlo()  # Identify yourself to the server
        server.starttls()  # Enable TLS encryption
        server.ehlo()  # Re-identify yourself over TLS connection
        
        print(f"Logging in to {EMAIL_HOST} with user {EMAIL_HOST_USER}...")
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_HOST_USER
        msg['To'] = to_email
        msg['Subject'] = "Test Email from Medical Cabinet"
        
        body = "This is a test email from your Medical Cabinet application."
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        print(f"Sending email from {EMAIL_HOST_USER} to {to_email}...")
        server.sendmail(EMAIL_HOST_USER, to_email, msg.as_string())
        server.quit()
        
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Email failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Medical Cabinet Notification Test")
    print("================================")
    
    while True:
        print("\nSelect an option:")
        print("1. Test Twilio SMS")
        print("2. Test Email")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == "1":
            test_twilio()
        elif choice == "2":
            test_email()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
