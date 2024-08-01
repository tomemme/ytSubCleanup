from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle
import os
import datetime
import time

# API credentials
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
PROCESSED_CHANNELS_FILE = 'processed_channels.txt'
INACTIVE_CHANNELS_FILE = 'inactive_channels.txt'
API_REQUEST_LIMIT = 9500

# Authenticates the user and returns an authorized YouTube API service.
def get_authenticated_service():
    creds = None
    # Load credentials from 'token.pickle' if they exist
    if os.path.exists('token.pickle'):
        print("Loading credentials from token.pickle...")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no valid credentials available, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("Running OAuth flow to get new credentials...")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future runs
        print("Saving credentials to token.pickle...")
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('youtube', 'v3', credentials=creds)

# Fetches the date of the last video uploaded by the given channel.
def get_channel_last_video_date(service, channel_id):
    
    request = service.search().list(
        part='snippet',
        channelId=channel_id,
        maxResults=1,
        order='date'
    )
    response = request.execute()
    if response['items']:
        return response['items'][0]['snippet']['publishedAt']
    else:
        return None

# Fetches all the subscriptions of the authenticated user.
def get_all_subscriptions(service, processed_channels):

    subscriptions = []
    request = service.subscriptions().list(
        part='snippet',
        mine=True,
        maxResults=50  # updated to 50 to reduce request
    )

    while request is not None:
        print("Making API request to fetch subscriptions...")
        response = request.execute()
        for item in response['items']:
            channel_id = item['snippet']['resourceId']['channelId']
            if channel_id not in processed_channels:
                subscriptions.append(item)
        request = service.subscriptions().list_next(request, response)
        time.sleep(1)  # Delay to avoid hitting the rate limit

    return subscriptions

# Main function to authenticate the user, fetch subscriptions, and check the last video date.
def main():
    
    print("Authenticating...")
    service = get_authenticated_service()
    print("Fetching subscriptions...")

    # Load the list of processed channels if it exists
    processed_channels = set()
    if os.path.exists(PROCESSED_CHANNELS_FILE):
        with open(PROCESSED_CHANNELS_FILE, 'r') as f:
            processed_channels = set(line.strip() for line in f)

    subscriptions = get_all_subscriptions(service, processed_channels)
    
    print("Retrieved subscriptions:")
    api_request_count = 0  # Track the number of API requests
    inactive_channels = []

    try:
        for item in subscriptions:
            channel_id = item['snippet']['resourceId']['channelId']
            channel_title = item['snippet']['title']

            if api_request_count >= API_REQUEST_LIMIT:
                print("Approaching API quota limit. Stopping further requests.")
                break

            print(f"Checking channel: {channel_title} (ID: {channel_id})")
            last_video_date = get_channel_last_video_date(service, channel_id)
            api_request_count += 1

            if last_video_date:
                last_video_date = datetime.datetime.strptime(last_video_date, "%Y-%m-%dT%H:%M:%SZ")
                if last_video_date < datetime.datetime.now() - datetime.timedelta(days=730):
                    print(f"Unsubscribe from: {channel_title} (Last video: {last_video_date})")
                    inactive_channels.append(f"{channel_title} (Last video: {last_video_date})")
            else:
                print(f"Unsubscribe from: {channel_title} (No videos found)")
                inactive_channels.append(f"{channel_title} (No videos found)")

            processed_channels.add(channel_id)
            time.sleep(1)  # Delay to avoid hitting the rate limit
    finally:
        # Save the list of inactive channels to a file
        with open(INACTIVE_CHANNELS_FILE, 'a') as f:
            for channel in inactive_channels:
                f.write(channel + "\n")

        # Save the list of processed channels to a file
        with open(PROCESSED_CHANNELS_FILE, 'a') as f:
            for channel_id in processed_channels:
                f.write(channel_id + "\n")

        print("Progress has been saved to files.")

if __name__ == '__main__':
    main()
