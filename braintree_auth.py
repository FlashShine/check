import httpx
import base64
import json
import re

async def get_braintree_auth():
    headers = {
        'authority': 'www.calipercovers.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    }

    async with httpx.AsyncClient() as client:
        r1 = await client.get('https://www.calipercovers.com/my-account/', headers=headers)
        
        # Extract the Braintree token from the response
        token_match = re.search(r'var wc_braintree_client_token = \["(.*?)"\];', r1.text)
        if not token_match:
            return None  # Return None if token extraction fails

        token = token_match.group(1)
        decoded_token = json.loads(base64.b64decode(token))

        return decoded_token.get("authorizationFingerprint")  # Return authorization fingerprint
