import sys
import requests
import json

def update_nameservers(domain, api_key, secret_key, nameservers):
    url = f"https://porkbun.com/api/json/v3/dns/setNameservers/{domain}"
    
    payload = {
        "apikey": api_key,
        "secretapikey": secret_key,
        "nameservers": nameservers
    }
    
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Error updating nameservers: {response.text}")
        sys.exit(1)
    print("Nameservers updated successfully!")

if __name__ == "__main__":
    domain = sys.argv[1]
    api_key = sys.argv[2]
    secret_key = sys.argv[3]
    nameservers = sys.argv[4:]
    update_nameservers(domain, api_key, secret_key, nameservers) 