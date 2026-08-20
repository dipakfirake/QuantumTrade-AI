"""
Fyers API v3 Authentication Helper

This script generates your daily Access Token for Fyers API v3 and saves it to .env.
"""
import os
import webbrowser
from fyers_apiv3 import fyersModel

def load_env_vars():
    """Load key-value pairs from .env if present."""
    env = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env

def fyers_login():
    print("=" * 60)
    print("        FYERS API v3 - Quick Authentication Setup")
    print("=" * 60)
    
    env = load_env_vars()
    app_id = env.get("FYERS_API_KEY", "")
    secret_key = env.get("FYERS_SECRET_KEY", "")
    
    if app_id and secret_key:
        print(f"Loaded credentials from .env:")
        print(f"  App ID: {app_id}")
        print(f"  Secret: {'*' * (len(secret_key) - 4) + secret_key[-4:] if len(secret_key) > 4 else '****'}")
    else:
        app_id = input("\nEnter your Fyers App ID (e.g. XXXXXX-100): ").strip()
        secret_key = input("Enter your Fyers Secret Key: ").strip()
    
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
    print("3. After successful login, you will be redirected to trade.fyers.in.")
    print("4. Copy the 'auth_code' parameter from the redirected browser URL bar.")
    print("   Example: https://trade.fyers.in/.../?auth_code=eyJ0eXAiOiJKV1...")
    
    auth_code = input("\nEnter the auth_code from browser URL: ").strip()
    
    if not auth_code:
        print("[Error] Auth code cannot be empty.")
        return
    
    # If full URL pasted, extract auth_code
    if "auth_code=" in auth_code:
        auth_code = auth_code.split("auth_code=")[1].split("&")[0]
    
    session.set_token(auth_code)
    response = session.generate_token()
    
    if isinstance(response, dict) and "access_token" in response:
        access_token = response["access_token"]
        print("\n" + "=" * 60)
        print("SUCCESS! Generated Fyers Access Token:")
        print(f"Access Token: {access_token[:20]}...{access_token[-10:]}")
        print("=" * 60)
        
        # Update .env file
        env_content = f"""FYERS_API_KEY={app_id}
FYERS_SECRET_KEY={secret_key}
FYERS_ACCESS_TOKEN={access_token}
USE_BROKER_ETQ=True
ETQ_MODE=fyers
"""
        with open(".env", "w") as f:
            f.write(env_content)
        
        print("\n✅ Saved Access Token to .env file!")
        print("You can now run: python -m streamlit run app.py")
    else:
        print("\n[Error] Failed to generate token:")
        print(response)

if __name__ == "__main__":
    fyers_login()
