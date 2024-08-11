from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import google.auth.exceptions
import pickle
import os
import datetime
import time
import json

# API credentials
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
PROCESSED_CHANNELS_FILE = 'processed_channels.txt'
INACTIVE_CHANNELS_FILE = 'inactive_channels.txt'
SUBSCRIPTIONS_FILE = 'subscriptions.json'
ERROR_CHANNELS_FILE = 'error_channels.txt'
API_REQUEST_LIMIT = 9500  # Safe margin to stop before hitting the daily quota

def get_authenticated_service():
    """
    Authenticates the user and returns an authorized YouTube API service.
    """
    creds = None
    if os.path.exists('token.pickle'):
        print("Loading credentials from token.pickle...")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Refreshing expired credentials...")
                creds.refresh(Request())
            except google.auth.exceptions.RefreshError:
                print("Failed to refresh credentials, running OAuth flow to get new credentials...")
                creds = None
        if not creds:
            print("Running OAuth flow to get new credentials...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        print("Saving credentials to token.pickle...")
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('youtube', 'v3', credentials=creds)

def get_channel_last_video_date(service, channel_id):
    """
    Fetches the date of the last video uploaded by the given channel.
    """
    request = service.search().list(
        part='snippet',
        channelId=channel_id,
        maxResults=1,
        order='date'
    )
    response = request.execute()
    if response['items']:
        snippet = response['items'][0]['snippet']
        published_at = snippet.get('publishedAt')
        video_id = response['items'][0].get('id', {}).get('videoId')
        return published_at, video_id
    else:
        return None, None

def get_video_details(service, video_id):
    """
    Fetches the details of the given video.
    """
    request = service.videos().list(
        part='contentDetails',
        id=video_id
    )
    response = request.execute()
    if response['items']:
        duration = response['items'][0]['contentDetails']['duration']
        return duration
    return None

def fetch_subscriptions(service):
    """
    Fetches all the subscriptions of the authenticated user.
    """
    subscriptions = []
    request = service.subscriptions().list(
        part='snippet',
        mine=True,
        maxResults=50
    )

    while request is not None:
        print("Making API request to fetch subscriptions...")
        response = request.execute()
        subscriptions.extend(response['items'])
        request = service.subscriptions().list_next(request, response)
        time.sleep(1)

    return subscriptions

def load_subscriptions():
    """
    Loads the list of subscriptions from a file.
    """
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_subscriptions(subscriptions):
    """
    Saves the list of subscriptions to a file.
    """
    with open(SUBSCRIPTIONS_FILE, 'w') as f:
        json.dump(subscriptions, f)

def main():
    """
    Main function to authenticate the user, fetch subscriptions, and check the last video date.
    """
    print("Authenticating...")
    service = get_authenticated_service()

    # Load subscriptions from file or fetch if not already saved
    subscriptions = load_subscriptions()
    if not subscriptions:
        print("Fetching subscriptions...")
        subscriptions = fetch_subscriptions(service)
        save_subscriptions(subscriptions)
    else:
        print("Loaded subscriptions from file.")

    print("Retrieved subscriptions:")
    api_request_count = 0  # Track the number of API requests
    inactive_channels = []
    processed_channels = set()
    error_channels = []

    # Load the list of processed channels if it exists
    if os.path.exists(PROCESSED_CHANNELS_FILE):
        with open(PROCESSED_CHANNELS_FILE, 'r') as f:
            processed_channels = set(line.strip() for line in f)

    try:
        for item in subscriptions:
            channel_id = item['snippet']['resourceId']['channelId']
            channel_title = item['snippet']['title']

            if channel_id in processed_channels:
                continue

            if api_request_count >= API_REQUEST_LIMIT:
                print("Approaching API quota limit. Stopping further requests.")
                break

            print(f"Checking channel: {channel_title} (ID: {channel_id})")
            last_video_date, last_video_id = get_channel_last_video_date(service, channel_id)
            api_request_count += 1

            if last_video_date:
                last_video_date = datetime.datetime.strptime(last_video_date, "%Y-%m-%dT%H:%M:%SZ")
                if last_video_id:
                    video_duration = get_video_details(service, last_video_id)
                    if video_duration and 'PT1M' in video_duration:  # This checks if the video is a short (less than 1 minute)
                        print(f"Channel {channel_title} mostly posts Shorts.")
                        # Handle Shorts-specific logic if needed
                if last_video_date < datetime.datetime.now() - datetime.timedelta(days=365):
                    print(f"Unsubscribe from: {channel_title} (Last video: {last_video_date})")
                    inactive_channels.append(f"{channel_id} (Last video: {last_video_date})")
            else:
                print(f"Unsubscribe from: {channel_title} (No videos found)")
                inactive_channels.append(f"{channel_id} (No videos found)")

            processed_channels.add(channel_id)
            time.sleep(1)
    except Exception as e:
        print(f"Error processing channel {channel_title} (ID: {channel_id}): {e}")
        error_channels.append(f"{channel_title} (ID: {channel_id})")
    finally:
        # Save the list of inactive channels to a file
        with open(INACTIVE_CHANNELS_FILE, 'a') as f:
            for channel in inactive_channels:
                f.write(channel + "\n")

        # Save the unique list of processed channels to a file
        with open(PROCESSED_CHANNELS_FILE, 'w') as f:
            for channel_id in processed_channels:
                f.write(channel_id + "\n")

        # Save the list of channels that caused errors
        if error_channels:
            with open(ERROR_CHANNELS_FILE, 'a') as f:
                for channel in error_channels:
                    f.write(channel + "\n")

        print("Progress has been saved to files.")

if __name__ == '__main__':
    main()
