import sys
import requests
import json

def update_nameservers(domain, api_key, secret_key, nameservers):
    url = f"https://api.porkbun.com/api/json/v3/domain/updateNs/{domain}"
    
    # Match the exact payload structure that worked in PowerShell
    payload = {
        "secretapikey": secret_key,
        "apikey": api_key,
        "ns": nameservers
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    
    if response_data.get('status') != 'SUCCESS':
        print(f"Error updating nameservers: {response.text}")
        sys.exit(1)
    print(f"Nameservers update: {response_data.get('message')}")

if __name__ == "__main__":
    domain = sys.argv[1]
    api_key = sys.argv[2]
    secret_key = sys.argv[3]
    nameservers = sys.argv[4:]
    update_nameservers(domain, api_key, secret_key, nameservers) 