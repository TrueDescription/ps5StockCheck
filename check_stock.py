import time
import random

def main():
    print(f"Triggered by: {EVENT_NAME or 'manual'}")
    
    # 1. Cache-Busting: Append a random number to the URL to force MTC to give us a fresh page
    cache_buster = f"?v={random.randint(10000, 99999)}"
    test_url = URL + cache_buster
    print(f"Checking URL: {test_url}")

    response = requests.get(test_url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 2. Diagnostics: Print the title of the page GitHub is actually seeing
    page_title = soup.title.text.strip() if soup.title else "NO TITLE FOUND"
    print(f"Page Title Seen by GitHub: '{page_title}'")
    
    if "Just a moment" in page_title or "Cloudflare" in page_title:
        print("🚨 ALERT: GitHub is being blocked by a Cloudflare bot check! 🚨")
        
    is_in_stock = False
    
    # Parse the JSON structured data
    json_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_scripts:
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
            graph = data.get('@graph', [data])
            for item in graph:
                if item.get('@type') == 'Product':
                    offers = item.get('offers', [{}])
                    if isinstance(offers, dict):
                        offers = [offers]
                    for offer in offers:
                        availability = offer.get('availability', '')
                        if 'InStock' in availability:
                            is_in_stock = True
        except json.JSONDecodeError:
            continue
            
    if is_in_stock:
        print("Result: IN STOCK")
        send_discord_msg(f"🚨 **ITEM IS IN STOCK!** 🚨\nGrab it here: {URL}")
    else:
        print("Result: OUT OF STOCK")

if __name__ == "__main__":
    main()
