"""
Fyers API v3 Authentication Helper

This script generates your daily Access Token for Fyers API v3 and saves it to .env.

Steps:
1. Go to https://myapi.fyers.in/ and create an App (or use existing).
   - App Type: Web App
   - Redirect URL: https://trade.fyers.in/api-login/redirect-uri/index.html
2. Run this script:
   python scripts/fyers_login.py
3. Follow the prompt to login and paste the generated auth code.
"""
import os
import webbrowser
from fyers_apiv3 import fyersModel

def fyers_login():
    print("=" * 60)
    print("        FYERS API v3 - Quick Authentication Setup")
    print("=" * 60)
    
    app_id = input("\nEnter your Fyers App ID (e.g. XXXXXX-100): ").strip()
    secret_key = input("Enter your Fyers Secret Key: ").strip()
    redirect_uri = input("Enter Redirect URI [default: https://trade.fyers.in/api-login/redirect-uri/index.html]: ").strip()
    
    if not redirect_uri:
        redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"
    
    session = fyersModel.SessionModel(
        client_id=app_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type="code",
        grant_type="authorization_code"
    )
    
    # Generate Auth Code URL
    auth_url = session.generate_authcode()
    print("\n" + "-" * 60)
    print("1. Opening Fyers Login page in your browser...")
    print(f"URL: {auth_url}")
    print("-" * 60)
    
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass
    
    print("\n2. Log in with your Fyers credentials (Mobile + OTP/PIN).")
    print("3. After successful login, you will be redirected.")
    print("4. Copy the 'auth_code' parameter from the redirected browser URL bar.")
    print("   Example: https://trade.fyers.in/api-login/redirect-uri/index.html?auth_code=eyJ0eXAiOiJKV1...")
    
    auth_code = input("\nEnter the auth_code from browser URL: ").strip()
    
    if not auth_code:
        print("[Error] Auth code cannot be empty.")
        return
    
    # If full URL pasted, extract auth_code
    if "auth_code=" in auth_code:
        auth_code = auth_code.split("auth_code=")[1].split("&")[0]
    
    session.set_token(auth_code)
    response = session.generate_token()
    
    if "access_token" in response:
        access_token = response["access_token"]
        print("\n" + "=" * 60)
        print("SUCCESS! Generated Fyers Access Token:")
        print(f"Access Token: {access_token[:20]}...{access_token[-10:]}")
        print("=" * 60)
        
        # Save to .env
        env_content = f"""FYERS_API_KEY={app_id}
FYERS_SECRET_KEY={secret_key}
FYERS_ACCESS_TOKEN={access_token}
USE_BROKER_ETQ=True
ETQ_MODE=fyers
"""
        with open(".env", "w") as f:
            f.write(env_content)
        
        print("\nSaved credentials to .env file.")
        print("You are now ready to run with live Fyers WebSocket market data!")
    else:
        print("\n[Error] Failed to generate token:")
        print(response)

if __name__ == "__main__":
    fyers_login()
