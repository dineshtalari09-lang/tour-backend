import json
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Tour AI is running 🚀"}


# ----------------------------
# Google Places
# ----------------------------
def get_places(city):
    google_key = os.getenv("GOOGLE_API_KEY")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    params = {
        "query": f"top tourist places in {city}",
        "key": google_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    places = []

    for place in data.get("results", [])[:5]:
        places.append(place["name"])

    return places


# ----------------------------
# YouTube Videos
# ----------------------------
def get_youtube_videos(place_name):
    google_key = os.getenv("GOOGLE_API_KEY")

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": f"{place_name} travel guide",
        "type": "video",
        "maxResults": 2,
        "key": google_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    videos = []

    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        videos.append(f"https://www.youtube.com/watch?v={video_id}")

    return videos


# ----------------------------
# Cost Estimation Tool
# ----------------------------
def estimate_trip_cost(city, days):

    base_per_day = 3000  # ₹ per day estimate

    total_cost = base_per_day * days

    breakdown = {
        "city": city,
        "days": days,
        "estimated_total_cost": total_cost,
        "breakdown": {
            "stay": int(total_cost * 0.4),
            "food": int(total_cost * 0.2),
            "travel": int(total_cost * 0.2),
            "activities": int(total_cost * 0.2)
        }
    }

    return breakdown


# ----------------------------
# AI Agent Endpoint
# ----------------------------
@app.get("/plan")
def plan(query: str):

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_places",
                "description": "Get top tourist places for a given city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"}
                    },
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_youtube_videos",
                "description": "Get travel guide YouTube videos for a place",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "place_name": {"type": "string"}
                    },
                    "required": ["place_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "estimate_trip_cost",
                "description": "Estimate approximate total trip cost for a city based on number of days",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "days": {"type": "integer"}
                    },
                    "required": ["city", "days"]
                }
            }
        }
    ]

    messages = [
        {
            "role": "system",
            "content": "You are an intelligent luxury travel planning AI agent. Use tools when needed to gather real-world information before answering."
        },
        {
            "role": "user",
            "content": query
        }
    ]

    while True:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        if message.tool_calls:

            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls
            })

            for tool_call in message.tool_calls:

                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                if tool_name == "get_places":
                    result = get_places(**tool_args)

                elif tool_name == "get_youtube_videos":
                    result = get_youtube_videos(**tool_args)

                elif tool_name == "estimate_trip_cost":
                    result = estimate_trip_cost(**tool_args)

                else:
                    result = "Tool not found"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

        else:
            return {"response": message.content}