
# This script gets the video length and caption ids for the videos in the video list

import os
import json
from dotenv import load_dotenv
import pandas as pd
from google.auth.transport.requests import Request as AuthRequest
from googleapiclient.discovery import build
import httplib2
from pprint import pprint
from datetime import timedelta
import re
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Access API key
yt_api_key = os.getenv("YOUTUBE_API_KEY")

# Create a YouTube API client
youtube = build('youtube', 'v3', developerKey=yt_api_key)

# Load videos list
try:
    videos_with_captions = pd.read_csv('../resources/video_list/videos_with_captions.csv', index_col=0)
    print('Succcessfully loaded videos with captions')
    loaded = videos_with_captions.copy()

except:
    videos_df = pd.read_csv('../resources/video_list/videos.csv', index_col=0)
    print('No file found with caption details. Loaded base videos df')
    loaded = videos_df.copy()

if 'video_id' in loaded.columns:
    loaded.set_index('video_id', inplace=True)


### FUNCTIONS ### 

# Function for video details
def get_video_details(video_id):
    details = []

    # Retrieve video details
    request = youtube.videos().list(
        part="snippet,contentDetails",  # Include 'contentDetails' to get video duration
        id=video_id
    )
    
    # Create an HTTP instance
    http = httplib2.Http()
    headers = {'referer': 'https://youtube.com'}

    # Execute the request
    response, content = http.request(request.uri, method=request.method, body=request.body, headers=headers)
    response_data = json.loads(content)

    # Extract video details from the response
    for item in response_data['items']:
        duration_str = item['contentDetails']['duration']  # Duration is provided in ISO 8601 format
        video_length = parse_duration(duration_str)
        details.append({'video_id': video_id, 'length': str(video_length)})

    return details


# Function to parse duration string into timedelta object
def parse_duration(duration_str):
    # Regular expression to extract hours, minutes, and seconds
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)
    
    # Extract hours, minutes, and seconds
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    
    # Create a timedelta object with the parsed hours, minutes, and seconds
    duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    
    return duration


# Function for caption ids
def get_caption_ids(video_id):
    captions = []

    # Retrieve captions for the video
    request = youtube.captions().list(
        part="snippet",
        videoId=video_id
    )
    # Create an HTTP instance
    http = httplib2.Http()
    headers = {'referer': 'https://youtube.com'}

    try:
        # Execute the request
        response, content = http.request(request.uri, method=request.method, body=request.body, headers=headers)
        response_data = json.loads(content)
        # pprint(response_data)

        # Extract captions from the response
        for item in response_data['items']:
            caption_id = item['id']
            captions.append({'id': caption_id})
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"Failed video ID: {video_id}")

    return captions


### MAIN ###

# Test Frame
test_df = loaded.head(10)

#Set environment variable -- dev is for testing the code against the API in small batches to keep quota usage down
production = True

if production == True:
    df = loaded
    environment = 'production'
elif production == False:
    df = test_df.copy()
    environment = 'test'
else:
    print('Error: please set environment')

print(f'Working DataFrame currently set as: ---{environment.upper()}---')

df = df.loc[:, ~df.columns.str.contains('Unnamed')] # Drop any previously generated index duplicates
df.head()


for index, row in df.iterrows():
    if pd.isnull(row['length']) or pd.isnull(row['caption_id']):  # Check if either length or caption_id is null
        video_id = row['video_id']
        
        # Get video details if length is null
        if pd.isnull(row['length']):
            video_details = get_video_details(video_id)
            if video_details:
                video_length = video_details[0]['length']
                df.loc[index, 'length'] = video_length

        # Get captions if caption_id is null
        if pd.isnull(row['caption_id']):
            captions = get_caption_ids(video_id)
            if captions:
                caption_id = captions[0]['id']
                df.loc[index, 'caption_id'] = caption_id


null_length = df['length'].isnull().value_counts()
print(null_length)
null_caption = df['caption_id'].isnull().value_counts()
print(null_caption)


complete = df[df['length'].notnull() & df['caption_id'].notnull()]
stragglers = df[df['length'].isnull() | df['caption_id'].isnull()]

### Save outputs
df.to_csv('../resources/video_list/videos_with_captions.csv') 
stragglers.to_csv('../resources/video_list/incomplete.csv')
complete.to_csv('../resources/video_list/details_complete.csv')


