import requests
import json

def fetch_epg_data(epg_url):
    """
    Fetches EPG data from a given URL.
    """
    try:
        response = requests.get(epg_url)
        response.raise_for_status()  # Will raise an HTTPError if the request failed
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching EPG data: {e}")
        return None

def clean_and_structure_data(data):
    """
    Clean and structure the channel data:
    1. Remove duplicates based on 'cs' or 'ex_id'.
    2. Ensure each channel has a unique identifier.
    3. Reformat the data for further use.
    """
    # Step 1: Remove duplicates based on 'cs' or 'ex_id'
    unique_channels = {}
    for channel in data:
        # Check if the channel has a unique 'cs' (channel id) or 'ex_id'
        key = channel.get('cs', None) or channel.get('ex_id', None)
        
        if key and key not in unique_channels:
            unique_channels[key] = channel

    # Step 2: Ensure each channel has a unique identifier
    for idx, (key, channel) in enumerate(unique_channels.items()):
        # Add a unique identifier to each channel, if not present
        if 'unique_id' not in channel:
            channel['unique_id'] = f'channel_{idx + 1}'

    # Step 3: Reformat the data (optional)
    formatted_channels = [
        {
            "name": channel.get('name', 'Unknown Channel'),
            "id": channel.get('unique_id'),
            "stream_url": channel.get('url', 'No URL'),
            "logo": channel.get('logo', 'No Logo'),
            # Add any other necessary fields here
        }
        for channel in unique_channels.values()
    ]
    
    return formatted_channels

def save_cleaned_data(formatted_channels, filename='cleaned_channels.json'):
    """
    Save the cleaned and structured channel data to a JSON file.
    """
    with open(filename, 'w') as f:
        json.dump(formatted_channels, f, indent=4)
    print(f"Cleaned data saved to {filename}")

def main():
    # Example URL to fetch the EPG data
    epg_url = 'http://example.com/epg_data.json'  # Replace with your actual URL

    # Step 1: Fetch the EPG data
    epg_data = fetch_epg_data(epg_url)

    if epg_data:
        # Step 2: Clean and structure the fetched data
        cleaned_data = clean_and_structure_data(epg_data)

        # Step 3: Save the cleaned data to a file
        save_cleaned_data(cleaned_data)

if __name__ == '__main__':
    main()
