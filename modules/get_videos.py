import os
import json
from dotenv import load_dotenv
import pandas as pd
from google.auth.transport.requests import Request as AuthRequest
from googleapiclient.discovery import build
import httplib2
from pprint import pprint

# Load environment variables from .env file
load_dotenv()

# Access API key
yt_api_key = os.getenv("YOUTUBE_API_KEY")

# Create a YouTube API client
youtube = build('youtube', 'v3', developerKey=yt_api_key)

# create dictionary of playlist urls
# url_base = https://www.youtube.com/playlist?list=
playlist_urls = {'52_weeks' : 'PLBaMLrfToJyybUT18OE3fMomFb9XU0ffC',
                 '52_FAQ' : 'PLBaMLrfToJyxF2RznuIpcLyUpLU3kLueV',
                 '52_second_edition' : 'PLBaMLrfToJyyhebzEduI7AK0nWHMlcDgK',
                 '11_days' : 'PLBaMLrfToJyznPoFK7iyxmsOHqxcRrm5m',
                 'biome' : 'PLBaMLrfToJyyywPKnlV7P--e6VG3umjW6',
                 'interviews' : 'PLBaMLrfToJywZby8_bU4fFsCUAq9BANsz',
                 'MACNA' : 'PLBaMLrfToJyyToilXCR5jLFMoemxwAE8x',
                 'nutrients' : 'PLBaMLrfToJyzCXREqXjsl066OzEgvXfJr'
                 }

playlist_test = {'nutrients' : 'PLBaMLrfToJyzCXREqXjsl066OzEgvXfJr'}

# Function to retrieve video URLs and titles from a playlist
def get_playlist_videos(list_name, playlist_id):
    videos = []
    next_page_token = None

    # Create an HTTP instance
    http = httplib2.Http()

    # Retrieve videos in the playlist
    while True:
        # Create the request object
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=100,  # Adjust as needed
            pageToken=next_page_token
        )

        # Set the referer header to a valid domain
        headers = {'referer': 'https://youtube.com'}

        # Execute the request with the modified headers
        response, content = http.request(request.uri, method=request.method, body=request.body, headers=headers)
        
        # Parse the JSON response
        response_data = json.loads(content)
        
        # Print response data for debugging
        #pprint(response_data)

        # Extract video URLs from the response
        for item in response_data.get('items', []):
            video_id = item['snippet']['resourceId']['videoId']
            #video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_title = item['snippet']['title']
            videos.append({'playlist': list_name, 'title': video_title, 'video_id': video_id, 'transcribed': False})

        # Check if there are more pages of results
        next_page_token = response_data.get('nextPageToken')
        if not next_page_token:
            break

    return videos


# Initialize an empty list to store all video dictionaries
all_videos = []

# Iterate over the playlist IDs and retrieve videos
for name, id in playlist_urls.items():
    videos = get_playlist_videos(name, id)
    all_videos.extend(videos)  # Extend the list with videos from the current playlist

# Create a DataFrame from the list of dictionaries
videos_df = pd.DataFrame(all_videos)

# Save list
os.makedirs('../resources/video_list', exist_ok=True)
videos_df.to_csv('../resources/video_list/videos.csv', index=False)