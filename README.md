# YouTube Subscription Cleanup Script

## Overview

This Python script helps automate the process of cleaning up your YouTube subscriptions by identifying channels that haven't uploaded videos in over a year. The script stores information about inactive channels, including their channel ID and name and last video date, in a text file for easy review.

## Features

- **Automated Cleanup**: Identifies channels that haven't uploaded videos in over a year.
- **Customizable Quota Management**: Stops before hitting the YouTube Data API quota limit to avoid errors.
- **Error Handling**: Logs channels that cause errors during processing for later review.
- **Customizable Output**: Stores both the channel ID and name in the `inactive_channels.txt` file for easy reference.
- **Progress Tracking**: Tracks processed channels to avoid redundant checks across multiple runs.

## Installation

### Prerequisites

- Python 3.6+
- Google APIs Client Library for Python

### Setup

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/tomemme/ytSubCleanup.git
    cd youtube-subscription-cleanup
    ```

2. **Install Required Python Packages**:
    ```bash
    pip install --upgrade google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
    ```

3. **Set Up Google API Credentials**:
    - Go to the [Google Cloud Console](https://console.cloud.google.com/).
    - Create a new project and enable the YouTube Data API v3.
    - Create OAuth 2.0 credentials and download the `client_secret.json` file.
    - Place `client_secret.json` in the root directory of the project.

## Usage

### Running the Script

1. **Run the Script Manually**:
    ```bash
    python SubCleanup.py
    ```

### Customizing the Script

- **Change the Quota Limit**: Adjust the `API_REQUEST_LIMIT` variable to manage how close you want the script to get to the daily API quota.
- **Modify Time Threshold**: By default, the script checks for channels inactive for over a year. You can modify the `datetime.timedelta(days=365)` part in the script to change this threshold.

### Output Files

- **`inactive_channels.txt`**: Contains the IDs and names of channels that haven't uploaded videos in over a year.
- **`processed_channels.txt`**: Tracks channels that have been processed to avoid redundant checks.
- **`error_channels.txt`**: Logs channels that caused errors during processing.

### Handling Errors

If the script encounters any issues (e.g., hitting the API quota), it will stop execution and save progress. The `error_channels.txt` file will log any channels that caused problems, allowing you to review and address them.

## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue if you have any suggestions or find any bugs.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Google APIs Client Library for Python](https://github.com/googleapis/google-api-python-client) for enabling API access.
- [YouTube Data API](https://developers.google.com/youtube/v3) for providing the data.

