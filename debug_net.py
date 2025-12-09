
import socket
import requests
import streamlit as st
import os

print("--- NETWORK DEBUG ---")
try:
    url = "https://blhhkexoirxwiemqmyw.supabase.co"
    print(f"Target URL: {url}")
    
    hostname = "blhhkexoirxwiemqmyw.supabase.co"
    print(f"Resolving {hostname}...")
    ip = socket.gethostbyname(hostname)
    print(f"Resolved to IP: {ip}")
    
    print("Attempting HTTP Request...")
    resp = requests.get(url, timeout=5)
    print(f"Response Code: {resp.status_code}")
    print("SUCCESS: Connection established.")
    
except Exception as e:
    print(f"FAILURE: {e}")
    if "11001" in str(e):
        print("DIAGNOSIS: DNS Error. The URL is invalid or DNS is blocked/failing.")
