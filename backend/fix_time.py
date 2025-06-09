# This script will fix the datetime.time issue in views.py
import re

# Path to the views.py file
views_path = 'appointments/views.py'

# Read the file content
with open(views_path, 'r') as f:
    content = f.read()

# Replace datetime.time with time
# First make sure we have the correct import
if 'from datetime import datetime, timedelta, date' in content:
    content = content.replace(
        'from datetime import datetime, timedelta, date',
        'from datetime import datetime, timedelta, date, time'
    )

# Then fix the datetime.time calls
content = content.replace('datetime.time(hour=hour, minute=minute)', 'time(hour=hour, minute=minute)')

# Write the updated content back to the file
with open(views_path, 'w') as f:
    f.write(content)

print("Fixed datetime.time issue in views.py")
