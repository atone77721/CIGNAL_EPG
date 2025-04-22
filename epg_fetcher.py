import requests
from datetime import datetime, timedelta

# Function to fetch EPG data for a specific channel
def fetch_epg(name, cid, start, end):
    print(f"📡 Fetching EPG for {name} (ID: {cid})")
    url = (
        f"https://cignalepg-api.aws.cignal.tv/epg/getepg?cid={cid}"
        f"&from={start.strftime('%Y-%m-%dT00:00:00.000Z')}"
        f"&to={end.strftime('%Y-%m-%dT00:00:00.000Z')}"
        f"&pageNumber=1&pageSize=100"
    )
    try:
        # Disabling SSL certificate verification
        response = requests.get(url, verify=False)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Main function to process the channels and get the EPG data
def main():
    # Define the start and end date for the EPG fetch
    start = datetime.utcnow()
    end = start + timedelta(days=1)

    # Example channel data (you would replace this with your actual list of channels)
    channels = [
        {"name": "Bilyonaryoch", "cid": "Bilyonaryoch_cid"},
        {"name": "Rptv", "cid": "Rptv_cid"},
        {"name": "Truefmtv", "cid": "Truefmtv_cid"},
        # Add more channels as needed
    ]

    # Loop through each channel and fetch the EPG data
    for channel in channels:
        api_data = fetch_epg(channel["name"], channel["cid"], start, end)
        if api_data:
            print(f"EPG data for {channel['name']} fetched successfully.")
        else:
            print(f"Failed to fetch EPG data for {channel['name']}.")

if __name__ == "__main__":
    main()
