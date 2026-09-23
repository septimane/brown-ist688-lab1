import json
import streamlit as st
import requests
from openai import OpenAI

st.title("🧥 Lab 5 — What to Wear Bot")
st.write("Type a city and I will tell you what to wear and what to do outside today.")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
MODEL = "gpt-5-mini"
DEFAULT_LOCATION = "Syracuse, NY"


def get_current_weather(location=DEFAULT_LOCATION):
    """
    Get weather from wttr.in. No API key or account needed.

    The values returned here were picked because each one changes what you would
    wear or what you could do outside. Temperature alone is not enough. Feels-like
    accounts for wind chill. The daily high and low matter because someone leaving
    at 8am needs to dress for 5pm too. Chance of rain decides whether you take a
    jacket. UV index decides sunscreen and sunglasses.
    """
    url = f"https://wttr.in/{location}?format=j1"
    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        raise Exception(f"Could not find a location named {location}")

    try:
        data = response.json()
    except ValueError:
        raise Exception(f"Could not find a location named {location}")

    current = data["current_condition"][0]
    today = data["weather"][0]
    area = data["nearest_area"][0]

    rain_chances = [int(hour["chanceofrain"]) for hour in today["hourly"]]

    return {
        "location": f"{area['areaName'][0]['value']}, {area['country'][0]['value']}",
        "temperature": float(current["temp_F"]),
        "feels_like": float(current["FeelsLikeF"]),
        "description": current["weatherDesc"][0]["value"],
        "humidity": int(current["humidity"]),
        "wind_mph": float(current["windspeedMiles"]),
        "high_today": float(today["maxtempF"]),
        "low_today": float(today["mintempF"]),
        "max_chance_of_rain": max(rain_chances),
        "uv_index": int(current["uvIndex"]),
    }



weather_tool = {
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": (
            "Get today's weather for a location. Returns current temperature, what it "
            "feels like, the daily high and low, chance of rain, wind speed and UV index."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and region, for example 'Syracuse, NY' or 'Lima, Peru'.",
                }
            },
            "required": [],
        },
    },
}


city = st.text_input("Where are you?", DEFAULT_LOCATION)
go = st.button("What should I wear?")

if go and city:
    messages = [
        {
            "role": "system",
            "content": (
                "You help people decide what to wear and what to do outdoors. "
                "Use the weather tool whenever a location is mentioned or implied."
            ),
        },
        {"role": "user", "content": f"What should I wear today in {city}?"},
    ]

   
    first = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=[weather_tool],
        tool_choice="auto",
    )

    reply = first.choices[0].message

    if not reply.tool_calls:
        st.write(reply.content)
        st.stop()

    call = reply.tool_calls[0]
    args = json.loads(call.function.arguments or "{}")

    location = args.get("location") or DEFAULT_LOCATION

    try:
        weather = get_current_weather(location)
    except Exception as e:
        st.error(str(e))
        st.stop()

    with st.expander("Weather the bot used"):
        st.json(weather)

    messages.append({
        "role": "assistant",
        "tool_calls": [{
            "id": call.id,
            "type": "function",
            "function": {
                "name": call.function.name,
                "arguments": call.function.arguments,
            },
        }],
    })
    messages.append({
        "role": "tool",
        "tool_call_id": call.id,
        "content": json.dumps(weather),
    })
    messages.append({
        "role": "user",
        "content": (
            "Using that weather, tell me two things.\n"
            "1. What to wear today. Account for the high and the low, not just the "
            "current temperature, since I will be outside all day.\n"
            "2. Two or three outdoor activities that suit these conditions, and one "
            "to avoid.\n"
            "Keep it short and practical. No preamble."
        ),
    })

    st.subheader(f"For {weather['location']}")
    stream = client.chat.completions.create(model=MODEL, messages=messages, stream=True)
    st.write_stream(stream)
