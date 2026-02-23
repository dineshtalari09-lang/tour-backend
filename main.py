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

@app.get("/plan")
def plan(city: str):
    places = get_places(city)

    detailed_places = []

    for place in places:
        videos = get_youtube_videos(place)

        detailed_places.append({
            "name": place,
            "videos": videos
        })

    return {
        "city": city,
        "places": detailed_places
    }