from datetime import datetime, timedelta, timezone
import urllib.request
import json
import os
import argparse  # Standard library
import ctypes  # For changing wallpaper on Windows
from pathlib import Path

# Function to get sunrise and sunset times from the Sunrise-Sunset API
def get_sunrise_sunset(lat, lon):
    url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date=today"
    with urllib.request.urlopen(url) as response:
        data = json.load(response)
    
    sunrise_time_str = data["results"]["sunrise"]
    sunset_time_str = data["results"]["sunset"]
    
    today_date = datetime.now(timezone.utc).date()  # Get today's date in UTC
    
    sunrise_utc = datetime.strptime(sunrise_time_str, "%I:%M:%S %p").replace(year=today_date.year, month=today_date.month, day=today_date.day)
    sunset_utc = datetime.strptime(sunset_time_str, "%I:%M:%S %p").replace(year=today_date.year, month=today_date.month, day=today_date.day)
    
    return sunrise_utc, sunset_utc

# Unified all timezones (using timedelta instead of pytz)
def convert_utc_to_local(utc_time, timezone_offset):
    # Convert UTC time to local time by adding timezone offset
    local_time = utc_time + timezone_offset
    return local_time

# Function to get the current part of the day (sunrise, morning, noon, evening, sunset, night)
def get_day_period(current_time, sunrise, sunset):
    sunrise_end = sunrise + timedelta(minutes=30)  
    sunrise_start = sunrise - timedelta(minutes=30)  

    sunset_start = sunset - timedelta(minutes=30)  
    sunset_end = sunset + timedelta(minutes=30)  

    # Convert sunrise_start, sunrise_end, sunset_start, and sunset_end to the same timezone as current_time
    sunrise_start = sunrise_start.replace(tzinfo=current_time.tzinfo)
    sunrise_end = sunrise_end.replace(tzinfo=current_time.tzinfo)
    sunset_start = sunset_start.replace(tzinfo=current_time.tzinfo)
    sunset_end = sunset_end.replace(tzinfo=current_time.tzinfo)

    day_duration = sunset_start - sunrise_end

    morning_duration = day_duration * 0.25
    noon_duration = day_duration * 0.50
    evening_duration = day_duration * 0.25

    morning_end = sunrise_end + morning_duration
    noon_start = morning_end
    noon_end = noon_start + noon_duration
    evening_start = noon_end
    evening_end = evening_start + evening_duration

    # Determine the part of the day
    if current_time >= sunrise_start and current_time < sunrise_end:
        return "Sunrise"
    elif current_time >= sunrise_end and current_time < morning_end:
        return "Morning"  
    elif current_time >= noon_start and current_time < noon_end:
        return "Noon"
    elif current_time >= evening_start and current_time < evening_end:
        return "Evening"
    elif current_time >= sunset_start and current_time < sunset_end:
        return "Sunset" 
    else:
        return "Night"

# Function to set wallpaper based on the current period
def set_wallpaper(period):
    wallpaper_folder = Path("C://Users//Administrator//Desktop//Tasks//py//images")
    wallpaper_mapping = {
        "Sunrise": wallpaper_folder / "sunrise.png",
        "Morning": wallpaper_folder / "morning.png",
        "Noon": wallpaper_folder / "noon.png",
        "Evening": wallpaper_folder / "evening.png",
        "Sunset": wallpaper_folder / "sunset.png",
        "Night": wallpaper_folder / "night.png",
    }

    wallpaper_path = wallpaper_mapping.get(period, wallpaper_folder / "default.png")
    
    # Output the selected wallpaper image name to stdout
    print(wallpaper_path.name)
    
    # Change the wallpaper based on the operating system
    if os.name == 'nt':  # Windows
        ctypes.windll.user32.SystemParametersInfoW(20, 0, str(wallpaper_path), 0)
    elif os.name == 'posix':  # Linux (using `gsettings`)
        os.system(f"gsettings set org.gnome.desktop.background picture-uri file://{wallpaper_path}")
    else:
        print("Wallpaper change not supported for this OS")

# Main function to run everything dynamically based on lat and lon
def main(lat, lon):
    # Define the timezone offset for Amman (UTC+3)
    amman_tz = timedelta(hours=3)
    
    sunrise_utc, sunset_utc = get_sunrise_sunset(lat, lon)
    
    sunrise_local = convert_utc_to_local(sunrise_utc, amman_tz)
    sunset_local = convert_utc_to_local(sunset_utc, amman_tz)
    
    current_time = datetime.now(timezone.utc) + amman_tz  # Get current local time in Amman
    today_date = datetime.now(timezone.utc).date()  # Get today's date in UTC
    
    if sunrise_local > sunset_local:
        # If sunrise is after sunset, adjust the sunrise time to the same day as sunset
        sunrise_local = sunrise_local.replace(day=today_date.day)

    day_period = get_day_period(current_time, sunrise_local, sunset_local)
    set_wallpaper(day_period)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get sunrise and sunset times and change wallpaper based on the part of the day.")
    parser.add_argument("lat", type=float, help="Latitude of the location")
    parser.add_argument("lon", type=float, help="Longitude of the location")
    
    args = parser.parse_args()
    
    main(args.lat, args.lon)
