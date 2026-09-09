import os
import json
import requests
import sys
from bs4 import BeautifulSoup

DEFAULT_PS5_URL = (
    "https://mtcfactoryoutlet.com/product/"
    "playstation-5-ps5-disc-edition-console-cfi-1x15a-no-stand-included-2/"
)

WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
DISABLE_PING = os.environ.get("DISABLE_PING", "").lower() == "true"
EVENT_NAME = os.environ.get("EVENT_NAME", "")
CUSTOM_URL = os.environ.get("CUSTOM_URL", "").strip()

if EVENT_NAME == "schedule" or not CUSTOM_URL:
    URL = DEFAULT_PS5_URL
else:
    URL = CUSTOM_URL

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-CA,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def send_discord_msg(message):
    if DISABLE_PING:
        print("\n🔕 [SILENT MODE] Would have sent this message to Discord:")
        print(f'"{message}"\n')
        return

    if not WEBHOOK:
        print("No webhook URL configured.")
        return

    response = requests.post(
        WEBHOOK,
        json={"content": message},
        timeout=15,
    )
    response.raise_for_status()


def iter_json_nodes(value):
    """
    Recursively walk JSON-LD because @graph / offers / etc.
    may be dictionaries or lists.
    """
    if isinstance(value, dict):
        yield value

        for child in value.values():
            yield from iter_json_nodes(child)

    elif isinstance(value, list):
        for child in value:
            yield from iter_json_nodes(child)


def check_json_ld(soup):
    """
    JSON-LD fallback.
    Returns True/False if a stock state is found, otherwise None.
    """
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        raw = script.get_text(strip=True)

        if not raw:
            continue

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        for node in iter_json_nodes(data):
            node_type = node.get("@type", [])

            if isinstance(node_type, str):
                node_type = [node_type]

            if "Product" not in node_type:
                continue

            offers = node.get("offers", [])

            if isinstance(offers, dict):
                offers = [offers]

            if not isinstance(offers, list):
                continue

            for offer in offers:
                if not isinstance(offer, dict):
                    continue

                availability = str(offer.get("availability", ""))

                print(f"JSON-LD availability: {availability}")

                if availability.endswith("OutOfStock"):
                    return False

                if availability.endswith("InStock"):
                    return True

    return None


def detect_stock(soup):
    # ---------------------------------------------------------
    # 1. BEST SIGNAL:
    #    WooCommerce's stock element for the MAIN product.
    #
    # Typical examples:
    # <p class="stock in-stock">In stock</p>
    # <p class="stock out-of-stock">Out of stock</p>
    # ---------------------------------------------------------

    stock_element = soup.select_one(".summary .stock")

    if stock_element:
        classes = set(stock_element.get("class", []))
        text = " ".join(stock_element.stripped_strings).lower()

        print(f"Stock element text: {text!r}")
        print(f"Stock element classes: {sorted(classes)}")

        if "out-of-stock" in classes or "out of stock" in text:
            return False, "WooCommerce stock element"

        if "in-stock" in classes or text == "in stock":
            return True, "WooCommerce stock element"

    # ---------------------------------------------------------
    # 2. SECONDARY SIGNAL:
    #    An enabled Add to Cart button on the main product.
    # ---------------------------------------------------------

    add_to_cart = soup.select_one(
        "form.cart button.single_add_to_cart_button"
    )

    if add_to_cart:
        classes = set(add_to_cart.get("class", []))

        is_disabled = (
            add_to_cart.has_attr("disabled")
            or "disabled" in classes
        )

        print(
            "Add-to-cart button found "
            f"(disabled={is_disabled})"
        )

        if not is_disabled:
            return True, "enabled Add to Cart button"

    # ---------------------------------------------------------
    # 3. FALLBACK:
    #    Structured JSON-LD.
    # ---------------------------------------------------------

    json_result = check_json_ld(soup)

    if json_result is not None:
        return json_result, "JSON-LD"

    # Important:
    # Don't silently claim "out of stock" if we could not determine it.
    return None, "no recognizable stock indicator"


def main():
    print(f"Triggered by: {EVENT_NAME or 'manual'}")
    print(f"Checking URL: {URL}")

    response = requests.get(
        URL,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()

    print(f"HTTP status: {response.status_code}")
    print(f"Final URL: {response.url}")
    print(f"Downloaded: {len(response.text):,} bytes")

    soup = BeautifulSoup(response.text, "html.parser")

    is_in_stock, source = detect_stock(soup)

    print(f"Detection source: {source}")

    if is_in_stock is True:
        print("Result: IN STOCK")

        send_discord_msg(
            "🚨 **ITEM IS IN STOCK!** 🚨\n"
            f"Grab it here: {URL}"
        )

    elif is_in_stock is False:
        print("Result: OUT OF STOCK")

    else:
        print("Result: UNKNOWN")
        print(
            "⚠️ Could not find a recognized WooCommerce "
            "stock indicator on the page."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
