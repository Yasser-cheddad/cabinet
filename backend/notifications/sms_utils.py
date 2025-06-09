from twilio.rest import Client

def send_sms(to, body):
    account_sid = 'YOUR_TWILIO_SID'
    auth_token = 'YOUR_TWILIO_TOKEN'
    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        body=body,
        from_='+1234567890',
        to=to
    )
    return message.sid