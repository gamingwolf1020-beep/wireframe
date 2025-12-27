import json
import secrets
from datetime import datetime
import os

DATA_FILE = 'data.json'

# Mock Client Data
CLIENT_ID = "mock_client_001"
CLIENT_NAME = "StartUp Inc."

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "jobs": [], "proposals": []}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def seed_jobs():
    data = load_data()
    
    # Ensure mock client exists
    client_exists = False
    for user in data['users']:
        if user['id'] == CLIENT_ID:
            client_exists = True
            break
            
    if not client_exists:
        data['users'].append({
            "id": CLIENT_ID,
            "name": CLIENT_NAME,
            "email": "client@startup.inc",
            "password": "password",
            "role": "client",
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    example_jobs = [
        {
            "title": "Build a React Native E-commerce App",
            "category": "programming_tech",
            "budget": "1500",
            "deadline": "2025-01-20",
            "description": "We need a skilled mobile developer to build a cross-platform e-commerce app using React Native. Must include payment gateway integration."
        },
        {
            "title": "Logo Design for Tech Brand",
            "category": "graphics_design",
            "budget": "200",
            "deadline": "2025-12-25",
            "description": "Looking for a minimalist and modern logo for our new AI startup. Theme: Blue and Neon."
        },
        {
            "title": "SEO Optimization for Blog",
            "category": "digital_marketing",
            "budget": "300",
            "deadline": "2025-01-05",
            "description": "Improve ranking for our tech blog. Keywords analysis and on-page SEO required."
        },
        {
            "title": "Translate Legal Documents to Spanish",
            "category": "writing_translation",
            "budget": "100",
            "deadline": "2025-12-30",
            "description": "Certified translator needed for 10 pages of legal contracts."
        },
        {
            "title": "Explainer Video for SaaS Product",
            "category": "video_animation",
            "budget": "800",
            "deadline": "2025-01-15",
            "description": "Create a 60-second 2D animated explainer video for our dashboard software."
        },
        {
            "title": "Composer for Game Soundtrack",
            "category": "music_audio",
            "budget": "400",
            "deadline": "2025-02-01",
            "description": "Ambient sci-fi background music needed for an indie game."
        },
        {
            "title": "Virtual Assistant for Executives",
            "category": "business",
            "budget": "500",
            "deadline": "2025-01-10",
            "description": "Manage emails, schedule meetings, and travel arrangements for 2 executives."
        },
        {
            "title": "Data Scraper for Real Estate",
            "category": "data",
            "budget": "250",
            "deadline": "2025-12-28",
            "description": "Scrape property listings from 3 major real estate websites and export to CSV."
        },
         {
            "title": "Fine-tune LLM for Customer Support",
            "category": "data",
            "budget": "2000",
            "deadline": "2025-02-15",
            "description": "We need an AI engineer to fine-tune Llama-3 on our support tickets dataset."
        },
        {
            "title": "Online Fitness Coach",
            "category": "lifestyle",
            "budget": "150",
            "deadline": "2025-01-01",
            "description": "Create a personalized 4-week workout and nutrition plan."
        }
    ]

    for job in example_jobs:
        new_job = {
            "id": secrets.token_hex(8),
            "client_id": CLIENT_ID,
            "client_name": CLIENT_NAME,
            "title": job['title'],
            "category": job['category'],
            "budget": job['budget'],
            "deadline": job['deadline'],
            "description": job['description'],
            "posted_at": datetime.now().strftime("%Y-%m-%d")
        }
        data['jobs'].append(new_job)

    save_data(data)
    print("Database seeded successfully with example jobs!")

if __name__ == "__main__":
    seed_jobs()
