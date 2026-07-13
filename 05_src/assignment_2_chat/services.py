import json 

import chromadb
import requests

from config import CHROMA_DIR, COLLECTION_NAME, get_embedding


_chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)


def _get_collection():
    return _chroma_client.get_collection(name=COLLECTION_NAME)


# Service 1: weather via Open-Meteo (free public API)
# Service will accept a city name as input and return the current weather information for the chat model to interpret

def get_weather(city: str) -> str:
    try:
    # Step 1: Convert city name into latitude and longitude coordinates (which are required by the API)
        geo_response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city, # city name from user
                "count": 1 # return only the top matching location
            },
            timeout=15, # stop after 15 s if API does not respond
        ).json()

        geo = geo_response # keep response as geo to use later

        if not geo.get("results"):
            return json.dumps({"error": f"Sorry, no place called '{city}' was found."}) # send error message if the city was not able to be found
        
        place = geo["results"][0] # use the first located that matches

        lat, lon = place["latitude"], place["longitude"] # extract latitute and longitude for the weather API request

    # Step 2: Use coordinates (lat, lon) to request the weather data
        forecast = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                
                # Current weather variables requested:
                "current": (
                    "temperature_2m",
                    "apparent_temperature",
                    "precipitation",
                    "wind_speed_10m"
                    ),
                # Daily summary variables requested:
                "daily": (
                    "temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_probability_max"
                    ),
                # Get forcast for 1 day (i.e., today only)
                "forecast_days": 1,
                # Get forcast in location's timezone
                "timezone": "auto",
            },
            timeout=15, # stop after 15 s if API does not respond
        ).json()

        cur = forecast.get("current", {}) # get curent weather info from API response
        daily = forecast.get("daily", {}) # get today's forcast from API response

    # Step 3: Create a simplified dictionary containing only the information needed
        data = {
            "city": place.get("name"),
            "country": place.get("country"),
            "temperature_c": cur.get("temperature_2m"),
            "feels_like_c": cur.get("apparent_temperature"),
            "wind_kph": cur.get("wind_speed_10m"),
            "precipitation_mm": cur.get("precipitation"),
            "today_high_c": (daily.get("temperature_2m_max") or [None])[0],
            "today_low_c": (daily.get("temperature_2m_min") or [None])[0],
            "rain_chance_pct": (daily.get("precipitation_probability_max") or [None])[0],
        }

        return json.dumps(data) # convert dictionary into a JSON strong
    
    except Exception as exc:
        return json.dumps({"error": f"Sorry, weather lookup has failed: {exc}"}) # if error this is the message to return the user
    


 # Service 2: semantic city search
# Service will search a vector database of cities and use semantic similar to find cities that match the meaning of the query 
# (e.g. return cities that align with: "I am interested in a city that is affordable, safe and has good healthcare") 

def search_cities(query: str, keyword: str = "", top_n: int = 3) -> str:
    """Semantic search over the city vector.
    If `keyword` is given, documents will first be restricted to only those containing the term (lexical filter), 
    then the remaining cities will be ranked by semantic similarity to the query (hybrd search).
    """
    try:
    # Step 1: Load vector database
        collection = _get_collection()
    # Step 2: Convert user query into an embedding vector
        query_embedding = get_embedding(query)
    # Step 3: Define the semantic search parameters
        kwargs = {"query_embeddings": [query_embedding], "n_results": top_n}
    # STep 4: Apply optional keyword filter
        if keyword:
            kwargs["where_document"] = {"$contains": keyword}
    # Step 5: Query the vector database (compare the query embeddings against the stored city embeddings and return relevant matches)
        results = collection.query(**kwargs)

    # Step 6: Combine returned metadata and descriptions
        hits = []
        for i in range(len(results["ids"][0])):
            meta = dict(results["metadatas"][0][i])
            meta["description"] = results["documents"][0][i]
            hits.append(meta)
    # Step 7: If no suitable cities are found, return the a message to explain this.
        if not hits:
            return json.dumps({"results": [], "note": "No matching cities."})
    # Step 8: Return the matching cities and errors in JSON format
        return json.dumps({"results": hits})
    except Exception as exc:
        return json.dumps({"error": f"Search failed: {exc}"})
    


# Service 3: calculator for the cost of living in a city
# Estimates the total cost of living based on user inputs

def estimate_living_cost(
    months: int = 12, # number of months to estimate costs for
    people: int = 1, # number of people living in household
    monthly_rent: float = 1500.0, # monthly cost of rent
    monthly_food: float = 400.0, # monthly cost of food per person
    monthly_transport: float = 120.0, # monthly transportation cost per person
    monthly_misc: float = 300.0, # miscellaneous expense costs (e.g., leisure, fun, clothing)
) -> str:
    """Estimate the cost of living in a city."""

    try: # calculate total costs over the selected time period
        rent = months * monthly_rent # total cost of rent for household
        food = months * monthly_food * people # total cost of food for household
        transport = months * monthly_transport * people # total cost of transportation for household
        misc = months * monthly_misc * people # total miscellaneous costs for household

        total = rent + food + transport + misc # all costs added together

    # create a structured output containing the cost breakdown
        breakdown = {
            "months": months,
            "people": people,
            "housing_total": round(rent, 2),
            "food_total": round(food, 2),
            "transport_total": round(transport, 2),
            "misc_total": round(misc, 2),
            "total_cost": round(total, 2),
            "monthly_average": round(total / max(months, 1), 2),
            "currency": "USD",
        }
        return json.dumps(breakdown) # return outputs as JSON string
    except Exception as exc:     #  message to return if the calculation failed.
        return json.dumps({"error": f"Cost of living calculation failed: {exc}"})



# Tool schemas

TOOLS = [
    {
        "type": "function",
        "name": "get_weather",
        "description": (
            "Get the current weather and daily forecast for a city. This should be used whenever the user asks about weather in a city."
            ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Amsterdam'."}
            },
            "required": ["city"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_cities",
        "description": "Search a database of cities based on livability characteristics. Returns cities that match relevant metadata and descriptions.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language description of the type of city the user is looking for, including livabilty characteristics.",
                },
                "keyword": {
                    "type": "string",
                    "description": (
                        "Optional exact term the results must contain (e.g. a country, city or attribute) for a hybrid search. Use empty string if not needed."
                    ),
                },
                "top_n": {
                    "type": "integer",
                    "description": (
                        "How many cities to return (default 3)."
                        ),
                },
            },
            "required": ["query", "keyword", "top_n"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "estimate_living_cost",
        "description": (
            "Estimate the cost of living in a city based on household size and typical monthly expenses."
            ),
        "parameters": {
            "type": "object",
            "properties": {
                "months": {"type": "integer", "description": "Number of months to estimate living costs for."},
                "people": {"type": "integer", "description": "Number of people in household."},
                "monthly_rent": {"type": "number", "description": "Estimated monthly housing cost in USD."},
                "monthly_food": {"type": "number", "description": "Estimated monthly food cost per person in USD."},
                "monthly_transport": {"type": "number", "description": "Estimated monthly transportation cost per person in USD."},
                "monthly_misc": {"type": "number", "description": "Estimated monthly miscellaneous expenses per person in USD."},
            },
            "required": [
                "months",
                "people",
                "monthly_rent",
                "monthly_food",
                "monthly_transport",
                "monthly_misc",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

# Map tool names to the python functions that implement them.
TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "search_cities": search_cities,
    "estimate_living_cost": estimate_living_cost,
}