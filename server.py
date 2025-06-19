from typing import Any
import json
import sys
import httpx
from mcp.server.fastmcp import FastMCP

print("✅ server.py starting...", file=sys.stderr)

#Initialize the FastMCP server
mcp = FastMCP("weather")

# Constants
OPENMETEO_API_BASE = "https://api.open-meteo.com/v1"
USER_AGENT = "weather-app/1.0"

async def make_openmeteo_request(url: str) -> dict[str, Any] | None:
    """
    Sends an asynchronous GET request to the Open-Meteo API and returns the response as a JSON dictionary.

    Args:
        url (str): The full URL of the Open-Meteo API endpoint with query parameters.

    Returns:
        dict[str, Any] | None: A dictionary containing the parsed JSON response if the request is successful;
        otherwise, returns None in case of an error (e.g., timeout, connection error, invalid response).
    """

    # Define HTTP headers for the request
    headers = {
        "User-Agent": USER_AGENT,               # Custom user agent identifier           
        "Accept": "application/json"            # We expect a JSON response from the API
    }

    # Create an asynchronous HTTP client session
    async with httpx.AsyncClient() as client:
        try:
            # Send a GET request with headers and a timeout of 30 seconds
            response = await client.get(url, headers=headers, timeout=30.0)
            # Raise an exception if the response contains an HTTP error status (4xx or 5xx)
            response.raise_for_status()
            # Return the response content parsed as JSON
            return response.json()
        except Exception:
            # If an exception occurs (e.g., network error, invalid JSON), return None
            return None
        
# Register this function as a callable tool in the MCP server for use by language models
@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """
    Fetches and returns the weather forecast for a given geographic location using the Open-Meteo API.

    Args:
        latitude (float): Latitude of the desired location.
        longitude (float): Longitude of the desired location.

    Returns:
        str: A formatted string with daily forecast information (date, max/min temperature, precipitation, and weather code),
             or an error message if the forecast data could not be retrieved.
    """

    # Construct the request URL
    url = f"{OPENMETEO_API_BASE}/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,precipitation,weathercode&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&timezone=auto"
     # Call the Open-Meteo API and retrieve the response data
    data = await make_openmeteo_request(url)

    # Handle failure to retrieve data
    if not data:
        return "Unable to fetch forecast data for this location."

    # Format the daily forecast into a readable format
    daily = data["daily"]
    forecasts = []

    # Iterate over each day and format the forecast
    for i in range(len(daily["time"])):
        forecast = f"""
Date: {daily['time'][i]}
Max Temperature: {daily['temperature_2m_max'][i]}°C
Min Temperature: {daily['temperature_2m_min'][i]}°C
Precipitation: {daily['precipitation_sum'][i]} mm
Weather Code: {daily['weathercode'][i]}
"""
        forecasts.append(forecast)

    # Join the formatted forecast strings with separators
    return "\n---\n".join(forecasts)

# Register this function as a callable tool in the MCP server for use by language models
@mcp.tool()
async def get_current_weather(latitude: float, longitude: float) -> str:
    """
    Retrieves the current weather data for a given location using the Open-Meteo API.

    Args:
        latitude (float): Latitude of the target location.
        longitude (float): Longitude of the target location.

    Returns:
        str: A stringified version of the current weather data in JSON format,
             or an error message if the request fails.
    """
    # Construct the Open-Meteo API URL with desired weather variables
    url = f"{OPENMETEO_API_BASE}/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,is_day,showers,cloud_cover,wind_speed_10m,wind_direction_10m,pressure_msl,snowfall,precipitation,relative_humidity_2m,apparent_temperature,rain,weather_code,surface_pressure,wind_gusts_10m"
    # Send the HTTP request and await the response
    data = await make_openmeteo_request(url)

    # Handle the case where no data is returned
    if not data:
        return "Unable to fetch current weather data for this location."

    # Return the raw JSON data as a string
    return json.dumps(data, indent=2)

if __name__ == "__main__":
    print("✅ MCP server ready, running...", file=sys.stderr)
    # Entry point for launching the MCP server
    mcp.run(transport='stdio')