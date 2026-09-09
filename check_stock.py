import os
import requests
from bs4 import BeautifulSoup

URL = "https://mtcfactoryoutlet.com/product/playstation-5-ps5-disc-edition-console-cfi-1x15a-no-stand-included-2/"
WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
TEST_MODE = os.environ.get("TEST_MODE") == "true"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def send_discord_msg(message):
    if not WEBHOOK:
        print("No webhook URL found in environment variables.")
        return
    requests.post(WEBHOOK, json={"content": message})

def main():
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # WooCommerce standard indicators
    out_of_stock_tag = soup.find(class_="out-of-stock")
    add_to_cart_btn = soup.find(name="button", class_="single_add_to_cart_button")
    
    # Logic to determine stock
    is_in_stock = False
    if add_to_cart_btn:
        is_in_stock = True
    elif out_of_stock_tag and "Out of stock" in out_of_stock_tag.text:
        is_in_stock = False
    elif "Out of stock" not in response.text:
        is_in_stock = True
        
    if is_in_stock:
        print("Status: IN STOCK")
        send_discord_msg(f"🚨 **PS5 IS IN STOCK!** 🚨\nGrab it here: {URL}")
    else:
        print("Status: OUT OF STOCK")
        if TEST_MODE:
            print("Running in test mode. Sending test ping...")
            send_discord_msg(f"🛠️ **TEST RUN** 🛠️\nYour GitHub Action is working perfectly, but the PS5 is currently OUT OF STOCK.\nLink: {URL}")

if __name__ == "__main__":
    main()
