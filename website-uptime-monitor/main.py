
import requests
import time
from urllib.parse import urlparse

url = input("Enter website URL: ").strip()

if not url.startswith(("http://", "https://")):
    url = "https://" + url

if not urlparse(url).hostname:
    print("Invalid URL")
else:
    try:
        start = time.perf_counter()
        response = requests.get(url, timeout=10)
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\nStatus code: {response.status_code}")
        print(f"Response time: {elapsed:.2f} ms")

        if response.status_code < 400:
          print("Status: UP")
        else:
          print("Status: DOWN")

    except requests.exceptions.Timeout:
        print("Request timed out.")

    except requests.exceptions.ConnectionError:
        print("Could not connect to website.")

    except requests.exceptions.RequestException as error:
        print(f"Request failed: {error}")
