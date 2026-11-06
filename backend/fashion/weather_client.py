"""
Live Weather Client for Context Agent using Open-Meteo free API (No API key required)
"""

import httpx
from typing import Dict, Any, Optional

def fetch_live_weather(city: str = "New York") -> Dict[str, Any]:
    """
    Fetches real-time weather data for a given city via Open-Meteo API.
    Resolves city name to latitude/longitude, then gets temperature & condition.
    """
    try:
        # Step 1: Geocoding lookup for city coordinates
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        with httpx.Client(timeout=4.0) as client:
            geo_res = client.get(geo_url)
            if geo_res.status_code == 200:
                data = geo_res.json()
                if data.get("results"):
                    loc = data["results"][0]
                    lat = loc["latitude"]
                    lon = loc["longitude"]
                    city_name = loc.get("name", city)
                    country = loc.get("country", "")

                    # Step 2: Current weather forecast query
                    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                    w_res = client.get(weather_url)
                    if w_res.status_code == 200:
                        curr = w_res.json().get("current_weather", {})
                        temp_c = curr.get("temperature", 22.0)
                        w_code = curr.get("weathercode", 0)

                        # Translate WMO weather code into human readable condition & context rules
                        condition, constraints = parse_weather_code(w_code, temp_c)

                        return {
                            "city": f"{city_name}, {country}".strip(", "),
                            "temperature_c": temp_c,
                            "temperature_f": round((temp_c * 9/5) + 32, 1),
                            "condition": condition,
                            "weather_code": w_code,
                            "constraints": constraints,
                            "status": "live"
                        }
    except Exception as e:
        print(f"[Weather Client] Error fetching Open-Meteo weather for '{city}': {e}")

    # Fallback default weather
    return {
        "city": city,
        "temperature_c": 22.0,
        "temperature_f": 71.6,
        "condition": "Mild & Pleasant",
        "weather_code": 0,
        "constraints": ["Breathable fabrics recommended", "Light outerwear optional"],
        "status": "simulated"
    }


def parse_weather_code(code: int, temp_c: float) -> tuple[str, list[str]]:
    """
    Translates WMO Weather Interpretation Codes into fashion constraints.
    """
    constraints = []
    
    # Temperature based rules
    if temp_c < 10:
        constraints.append("Heavy outerwear required (coats/jackets)")
        constraints.append("Warm insulating layers & closed footwear")
    elif temp_c < 18:
        constraints.append("Light jacket, blazer, or cardigan recommended")
    elif temp_c > 28:
        constraints.append("Lightweight, breathable fabrics (linen/cotton)")
        constraints.append("Short sleeves or sleeveless tops preferred")

    # WMO Code based condition rules
    if code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        condition = "Raining / Wet"
        constraints.append("Avoid suede, canvas, or floor-length bottoms in rain")
        constraints.append("Water-resistant footwear recommended")
    elif code in [71, 73, 75, 77, 85, 86]:
        condition = "Snowy / Freezing"
        constraints.append("Heavy insulated boots and thick coat essential")
    elif code in [95, 96, 99]:
        condition = "Thunderstorm"
        constraints.append("Sturdy covered footwear & protective jacket needed")
    elif code in [1, 2, 3]:
        condition = "Partly Cloudy"
    elif code == 0:
        condition = "Clear & Sunny"
    else:
        condition = "Overcast"

    return condition, constraints
