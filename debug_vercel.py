import urllib.request
import urllib.error

url = 'https://local-shop-bot.vercel.app/login'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

try:
    with urllib.request.urlopen(req) as resp:
        print("Success 200:")
        print(resp.read().decode())
except urllib.error.HTTPError as e:
    print(f"Error Code: {e.code}")
    print("Response Body:")
    print(e.read().decode('utf-8', errors='ignore')[:1500])
