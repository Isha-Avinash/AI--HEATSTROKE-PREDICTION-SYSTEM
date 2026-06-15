import requests

def get_live_weather(city):
    """
    Fetches real-time temperature and humidity for a given city using wttr.in.
    Returns a dictionary with success status, temperature, humidity, and description.
    """
    if not city or city.strip() == "":
        return {
            "success": False,
            "temp": 30.0,
            "humidity": 50.0,
            "description": "Invalid city name",
            "city": "Unknown"
        }
        
    try:
        # Fetch weather using the free, keyless wttr.in JSON format API
        city_cleaned = city.strip().replace(" ", "+")
        url = f"https://wttr.in/{city_cleaned}?format=j1"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            temp = float(current['temp_C'])
            humidity = float(current['humidity'])
            desc = current['weatherDesc'][0]['value']
            
            return {
                "success": True,
                "temp": temp,
                "humidity": humidity,
                "description": desc,
                "city": city.title()
            }
    except Exception as e:
        # Fail gracefully
        print(f"Weather fetch exception: {e}")
        
    return {
        "success": False,
        "temp": 35.0, # Default hot-weather simulation fallback
        "humidity": 45.0,
        "description": "Offline (using default hot weather simulation)",
        "city": city.title()
    }