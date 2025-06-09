import os
import requests
import json
from datetime import datetime, timedelta

# Get tomorrow's date
tomorrow = datetime.now() + timedelta(days=1)
tomorrow_str = tomorrow.strftime('%Y-%m-%d')

# API endpoint
url = "http://localhost:8000/api/appointments/timeslots/create/"

# Get token from local storage (you'll need to manually enter this)
token = input("Enter your authentication token from browser localStorage: ")

# Request headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# Request data for a time slot tomorrow
data = {
    "doctor_id": 3,  # Replace with the actual doctor ID if needed
    "date": tomorrow_str,
    "start_time": "09:00:00",
    "end_time": "10:00:00",
    "is_available": True
}

print(f"Creating time slot for date: {tomorrow_str}")
print(f"Data being sent: {json.dumps(data, indent=2)}")

# Make the request
response = requests.post(url, headers=headers, json=data)

# Print the response
print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")

# If successful, let's create another time slot for testing
if response.status_code == 201:
    data["start_time"] = "10:00:00"
    data["end_time"] = "11:00:00"
    
    print("\nCreating second time slot...")
    print(f"Data being sent: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, headers=headers, json=data)
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
