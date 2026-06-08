import requests

def get_weather(city):
    try:
        url = f"https://wttr.in/{city}?format=3"
        return requests.get(url).text
    except:
        return "Weather data not available"