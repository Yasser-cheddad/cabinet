import requests
import json
from datetime import datetime, timedelta

# Get tomorrow's date
tomorrow = datetime.now() + timedelta(days=1)
tomorrow_str = tomorrow.strftime('%Y-%m-%d')

# API endpoint
url = "http://localhost:8000/api/appointments/timeslots/create/"

# Get the auth token from localStorage
# You'll need to replace this with your actual token
token = input("Enter your authentication token: ")

# Request headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# Request data
data = {
    "doctor_id": 3,  # Replace with the actual doctor ID
    "date": tomorrow_str,
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "is_available": True
}

# Make the request
response = requests.post(url, headers=headers, json=data)

# Print the response
print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")
