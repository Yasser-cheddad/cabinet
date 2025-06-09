"""
Test file to debug specific_time parsing logic
"""
from django.utils import timezone
from datetime import datetime, timedelta
import sys

def test_specific_time_parsing(specific_time_value, date_str=None):
    """Test the specific_time parsing logic with different inputs"""
    print(f"Testing specific_time: '{specific_time_value}', type: {type(specific_time_value)}")
    print(f"Testing date_str: '{date_str}'")
    
    try:
        # Ensure specific_time is a string and properly formatted
        specific_time_str = str(specific_time_value).strip() if specific_time_value else None
        
        if not specific_time_str:
            print("Error: specific_time is empty or None")
            return False
            
        # Check if the time format is valid (HH:MM)
        if ':' not in specific_time_str:
            print(f"Error: Time must be in HH:MM format, got: {specific_time_str}")
            return False
            
        parts = specific_time_str.split(':')
        if len(parts) != 2:
            print(f"Error: Time must have exactly one colon separator, got: {specific_time_str}")
            return False
            
        # Parse hour and minute
        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except ValueError as e:
            print(f"Error parsing hour/minute: {e}")
            return False
            
        # Validate hour and minute ranges
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            print(f"Error: Invalid hour/minute values: {hour}:{minute}")
            return False
            
        print(f"Success! Parsed time: {hour:02d}:{minute:02d}")
        
        # If we have a date_str, try to parse that too
        if date_str:
            try:
                appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                print(f"Success! Parsed date: {appointment_date}")
                
                # Create datetime objects with the specific time
                specific_start_time = datetime.combine(
                    appointment_date, 
                    datetime.time(hour=hour, minute=minute)
                )
                
                # Set end time to 30 minutes after start time
                specific_end_time = specific_start_time + timedelta(minutes=30)
                
                print(f"Success! Full datetime start: {specific_start_time}")
                print(f"Success! Full datetime end: {specific_end_time}")
            except ValueError as e:
                print(f"Error parsing date: {e}")
                return False
                
        return True
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

# Test cases
if __name__ == "__main__":
    # Test case 1: Normal time string
    test_specific_time_parsing("08:00", "2025-06-03")
    print("\n---\n")
    
    # Test case 2: Time string with spaces
    test_specific_time_parsing(" 09:30 ", "2025-06-03")
    print("\n---\n")
    
    # Test case 3: Invalid time format
    test_specific_time_parsing("8:00", "2025-06-03")
    print("\n---\n")
    
    # Test case 4: Non-string time value
    test_specific_time_parsing(800, "2025-06-03")
    print("\n---\n")
    
    # Test case 5: Invalid minute
    test_specific_time_parsing("08:60", "2025-06-03")
    print("\n---\n")
    
    # Test case 6: Invalid hour
    test_specific_time_parsing("24:00", "2025-06-03")
    print("\n---\n")
