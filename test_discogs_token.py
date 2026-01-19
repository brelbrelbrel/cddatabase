
import urllib.request
import json

DISCOGS_TOKEN = "WQDfPrbhGrmXKlPIFVRqmHKLDCdLNCobTYHTviKI"
USER_AGENT = "MusicDBCreator/1.0 +https://example.com"

def test_api():
    print("Testing Discogs Token...")
    
    # 1. Get Identity (User Profile)
    try:
        req = urllib.request.Request(
            "https://api.discogs.com/oauth/identity", 
            headers={'User-Agent': USER_AGENT, 'Authorization': f'Discogs token={DISCOGS_TOKEN}'}
        )
        with urllib.request.urlopen(req) as resp:
            identity = json.loads(resp.read().decode('utf-8'))
            username = identity['username']
            print(f"✅ Auth Success! User: {username}")
            print(f"   Resource URL: {identity['resource_url']}")
    except Exception as e:
        print(f"❌ Auth Failed: {e}")
        return

    # 2. Check Inventory (Read Access)
    try:
        inventory_url = f"https://api.discogs.com/users/{username}/inventory"
        req = urllib.request.Request(
            inventory_url, 
            headers={'User-Agent': USER_AGENT, 'Authorization': f'Discogs token={DISCOGS_TOKEN}'}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            count = data.get('pagination', {}).get('items', 0)
            print(f"✅ Inventory Access: TVOK! (Current items: {count})")
    except Exception as e:
        print(f"❌ Inventory Read Failed: {e}")

    # 3. Simulate Add Listing (Dry Run - just checking if we could technically form the request)
    # We won't actually post to avoid spamming, but we assume if (1) and (2) work, (3) is likely possible 
    # unless scope is restricted (which PATs usually aren't for personal use).
    print("ℹ️  Ready to implement listing creation.")

if __name__ == "__main__":
    test_api()
