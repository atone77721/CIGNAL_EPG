import requests
from datetime import datetime, timedelta
import pytz

# Function to fetch the EPG data for a channel
def fetch_epg(name, cid, start, end):
    print(f"📡 Fetching EPG for {name} (ID: {cid})")
    
    # Prepare the URL
    url = (
        f"https://cignalepg-api.aws.cignal.tv/epg/getepg?cid={cid}"
        f"&from={start.strftime('%Y-%m-%dT%H:%M:%S.000Z')}"
        f"&to={end.strftime('%Y-%m-%dT%H:%M:%S.000Z')}"
        f"&pageNumber=1&pageSize=100"
    )
    
    # Send the request to the API
    try:
        response = requests.get(url, verify=False)  # Disable SSL verification for testing purposes
        response.raise_for_status()  # Raise an exception for 4xx/5xx responses
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

    # Check if the response contains the 'data' field
    if response.status_code == 200:
        try:
            data = response.json()
            if 'data' in data:
                return data['data']
            else:
                print(f"No EPG data found for {name}.")
                return None
        except ValueError:
            print(f"Failed to parse JSON for {name}.")
            return None
    else:
        print(f"Failed to fetch EPG data for {name}. Status Code: {response.status_code}")
        return None

# Main function to process multiple channels
def main():
    # Define your channels and their corresponding `cid`
    channels = [
        {"name": "Bilyonaryoch", "cid": "Bilyonaryoch_cid"},
        {"name": "Rptv", "cid": "Rptv_cid"},
        {"name": "Truefmtv", "cid": "Truefmtv_cid"},
        # Add more channels as needed
    ]

    # Get the current time in UTC
    utc_now = datetime.now(pytz.utc)
    
    # Define the time window for EPG data (today's date, next 24 hours)
    start = utc_now
    end = utc_now + timedelta(days=1)

    # Iterate over each channel and fetch the EPG data
    for channel in channels:
        epg_data = fetch_epg(channel["name"], channel["cid"], start, end)
        
        if epg_data:
            print(f"EPG data for {channel['name']}:")
            print(epg_data)  # You can process this data as needed
        else:
            print(f"No data found for {channel['name']}")

if __name__ == "__main__":
    main()
