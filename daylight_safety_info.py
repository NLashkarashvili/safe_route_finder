from datetime import datetime, timedelta, time
import requests
import pytz

def fetch_sunrise_sunset(lat, lng, date):
    """Fetch sunrise and sunset times from the API and return them in UTC."""
    url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&date={date}&formatted=0"
    response = requests.get(url)
    data = response.json()
    
    if data['status'] != 'OK':
        raise Exception("Error fetching data from Sunrise-Sunset API")
    
    # Parse ISO 8601 format timestamps (API returns UTC times when formatted=0)
    sunrise_utc = datetime.fromisoformat(data['results']['sunrise'].replace('Z', '+00:00'))
    sunset_utc = datetime.fromisoformat(data['results']['sunset'].replace('Z', '+00:00'))
    
    return sunrise_utc, sunset_utc

def get_safety_level(current_time_utc, lat, lng):
    """
    Determine safety level based on time of day, automatically handling BST/GMT transitions.
    
    Args:
        current_time_utc (datetime): Current time in UTC
        lat (float): Latitude
        lng (float): Longitude
    
    Returns:
        str: Safety level ('Safe', 'Moderate Danger', or 'Most Danger')
    """
    # Use Europe/London timezone which automatically handles BST/GMT transitions
    london_tz = pytz.timezone('Europe/London')
    
    # Convert current UTC time to London local time (will be BST or GMT as appropriate)
    current_local_time = current_time_utc.astimezone(london_tz)
    
    # Fetch sunrise/sunset times for the current date
    current_date = current_local_time.strftime('%Y-%m-%d')
    sunrise_utc, sunset_utc = fetch_sunrise_sunset(lat, lng, current_date)
    
    # Convert sunrise/sunset times to London local time
    sunrise_local = sunrise_utc.astimezone(london_tz)
    sunset_local = sunset_utc.astimezone(london_tz)
    
    # Define time boundaries in local time
    current_date = current_local_time.date()
    early_morning_start = london_tz.localize(datetime.combine(current_date, time(5, 0)))
    early_morning_end = london_tz.localize(datetime.combine(current_date, time(6, 30)))
    late_night_start = london_tz.localize(datetime.combine(current_date, time(23, 30)))
    
    # Determine safety level based on the current time
    if early_morning_end <= current_local_time <= sunset_local:
        return 'Safe'
    elif early_morning_start <= current_local_time < early_morning_end or \
         sunset_local < current_local_time <= late_night_start:
        return 'Moderate Danger'
    else:
        return 'Most Danger'

def get_current_safety_info(lat, lng, current_time_utc=None):
    """
    Get comprehensive safety information including local time and BST/GMT status.
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        current_time_utc (datetime, optional): Current time in UTC for testing
    
    Returns:
        dict: Dictionary containing safety information
    """
    if current_time_utc is None:
        current_time_utc = datetime.now(pytz.UTC)
    
    london_tz = pytz.timezone('Europe/London')
    local_time = current_time_utc.astimezone(london_tz)
    
    # Check if we're in BST
    is_bst = local_time.dst() != timedelta(0)
    
    safety_level = get_safety_level(current_time_utc, lat, lng)
    
    return {
        'safety_level': safety_level,
        'local_time': local_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'is_bst': is_bst,
        'timezone_offset': f"{local_time.strftime('%z')} hours",
    }

if __name__ == "__main__":
    # Example coordinates for Camden, London
    lat = 51.5364
    lng = -0.1402
    
    # Get safety information
    safety_info = get_current_safety_info(lat, lng)
    
    print(f"Current local time: {safety_info['local_time']}")
    print(f"BST in effect: {safety_info['is_bst']}")
    print(f"Timezone offset: {safety_info['timezone_offset']}")
    print(f"Safety level: {safety_info['safety_level']}")
