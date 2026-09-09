import os
import requests
from bs4 import BeautifulSoup

DEFAULT_PS5_URL = "https://mtcfactoryoutlet.com/product/playstation-5-ps5-disc-edition-console-cfi-1x15a-no-stand-included-2/"

WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
DISABLE_PING = os.environ.get("DISABLE_PING") == "true"
EVENT_NAME = os.environ.get("EVENT_NAME", "")
CUSTOM_URL = os.environ.get("CUSTOM_URL", "").strip()

# Fork logic: if triggered by cron or no custom URL was entered, use the default PS5 URL
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
    
    out_of_stock_tag = soup.find(class_="out-of-stock")
    add_to_cart_btn = soup.find(name="button", class_="single_add_to_cart_button")
    
    is_in_stock = False
    if add_to_cart_btn:
        is_in_stock = True
    elif out_of_stock_tag and "Out of stock" in out_of_stock_tag.text:
        is_in_stock = False
    elif "Out of stock" not in response.text:
        is_in_stock = True
        
    if is_in_stock:
        print("Result: IN STOCK")
        send_discord_msg(f"🚨 **ITEM IS IN STOCK!** 🚨\nGrab it here: {URL}")
    else:
        print("Result: OUT OF STOCK")

if __name__ == "__main__":
    main()
