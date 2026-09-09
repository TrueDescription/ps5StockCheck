import os
import requests
import json
from bs4 import BeautifulSoup

DEFAULT_PS5_URL = "https://mtcfactoryoutlet.com/product/playstation-5-ps5-disc-edition-console-cfi-1x15a-no-stand-included-2/"

WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
DISABLE_PING = os.environ.get("DISABLE_PING") == "true"
EVENT_NAME = os.environ.get("EVENT_NAME", "")
CUSTOM_URL = os.environ.get("CUSTOM_URL", "").strip()

if EVENT_NAME == "schedule" or not CUSTOM_URL:
    URL = DEFAULT_PS5_URL
else:
    URL = CUSTOM_URL

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def send_discord_msg(message):
    if DISABLE_PING:
        print("\n🔕 [SILENT MODE] Would have sent this message to Discord:")
        print(f'"{message}"\n')
        return
        
    if not WEBHOOK:
        print("No webhook URL configured.")
        return
        
    requests.post(WEBHOOK, json={"content": message})

def main():
    print(f"Triggered by: {EVENT_NAME or 'manual'}")
    print(f"Checking URL: {URL}")

    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    is_in_stock = False
    
    # Find all the hidden JSON structured data scripts on the page
    json_scripts = soup.find_all('script', type='application/ld+json')
    
    for script in json_scripts:
        if not script.string:
            continue
            
        try:
            data = json.loads(script.string)
            # WooCommerce sometimes wraps data in a '@graph' list
            graph = data.get('@graph', [data])
            
            for item in graph:
                # Look specifically for the Product data block
                if item.get('@type') == 'Product':
                    offers = item.get('offers', [{}])
                    
                    # Ensure offers is a list to iterate over
                    if isinstance(offers, dict):
                        offers = [offers]
                        
                    for offer in offers:
                        # Extract the standardized availability URL
                        availability = offer.get('availability', '')
                        
                        # Schema.org standard is "http://schema.org/InStock" or "http://schema.org/OutOfStock"
                        if 'InStock' in availability:
                            is_in_stock = True
                            
        except json.JSONDecodeError:
            # If a block fails to parse, just skip it and check the next one
            continue
            
    if is_in_stock:
        print("Result: IN STOCK")
        send_discord_msg(f"🚨 **ITEM IS IN STOCK!** 🚨\nGrab it here: {URL}")
    else:
        print("Result: OUT OF STOCK")

if __name__ == "__main__":
    main()
