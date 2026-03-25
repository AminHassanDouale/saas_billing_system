"""
Quick connection test script.
Run from project root: python test_connection.py
"""

import sys

def check(label):
    print(f"\n{'='*50}")
    print(f"  {label}")
    print('='*50)

def ok(msg):
    print(f"  [OK]  {msg}")

def fail(msg):
    print(f"  [FAIL] {msg}")

def warn(msg):
    print(f"  [WARN] {msg}")


# ── 1. Config ────────────────────────────────────────────────────────────────
check("1. Loading config from .env")
try:
    from app.config import settings
    ok(f"App: {settings.APP_NAME}")
    ok(f"DB URL: {settings.DATABASE_URL}")
    ok(f"D-Money Base URL: {settings.DMONEY_BASE_URL}")
    ok(f"AppID: {settings.DMONEY_APPID}")
    ok(f"Merch Code: {settings.DMONEY_MERCH_CODE}")
    ok(f"X-App-Key: {settings.DMONEY_X_APP_KEY[:8]}...")
    ok(f"App Secret: {settings.DMONEY_APP_SECRET[:8]}...")
    ok(f"Private Key loaded: {'Yes' if settings.DMONEY_PRIVATE_KEY_B64 else 'MISSING'}")
    ok(f"Public Key loaded: {'Yes' if settings.DMONEY_PUBLIC_KEY_B64 else 'MISSING'}")
except Exception as e:
    fail(f"Config error: {e}")
    sys.exit(1)


# ── 2. Database ──────────────────────────────────────────────────────────────
check("2. MySQL Database (XAMPP)")
try:
    from app.database import engine
    with engine.connect() as conn:
        from sqlalchemy import text
        result = conn.execute(text("SELECT VERSION()"))
        version = result.fetchone()[0]
        ok(f"Connected! MySQL version: {version}")
except Exception as e:
    fail(f"Database connection failed: {e}")
    print("\n  Make sure:")
    print("  - XAMPP MySQL is running")
    print("  - Database 'saas_billing' exists in phpMyAdmin")
    print("  - DATABASE_URL in .env is correct")


# ── 3. Database Tables ───────────────────────────────────────────────────────
check("3. Database Tables")
try:
    from app.database import engine
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if tables:
        ok(f"Tables found: {', '.join(tables)}")
    else:
        warn("No tables found. Run: alembic upgrade head")
except Exception as e:
    fail(f"Could not inspect tables: {e}")


# ── 4. RSA Private Key ───────────────────────────────────────────────────────
check("4. RSA Private Key (signing)")
try:
    import base64
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    key_der = base64.b64decode(settings.DMONEY_PRIVATE_KEY_B64)
    private_key = serialization.load_der_private_key(key_der, password=None, backend=default_backend())
    key_size = private_key.key_size
    ok(f"Private key loaded successfully ({key_size}-bit RSA)")
except Exception as e:
    fail(f"Private key error: {e}")
    print("  Check DMONEY_PRIVATE_KEY_B64 in .env")


# ── 5. RSA Public Key ────────────────────────────────────────────────────────
check("5. RSA Public Key (verification)")
try:
    import base64
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    if settings.DMONEY_PUBLIC_KEY_B64:
        key_der = base64.b64decode(settings.DMONEY_PUBLIC_KEY_B64)
        public_key = serialization.load_der_public_key(key_der, backend=default_backend())
        ok(f"Public key loaded successfully ({public_key.key_size}-bit RSA)")
    else:
        warn("DMONEY_PUBLIC_KEY_B64 not set in .env")
except Exception as e:
    fail(f"Public key error: {e}")


# ── 6. D-Money Token ─────────────────────────────────────────────────────────
check("6. D-Money Gateway — Get Token (live API call)")
try:
    import requests, urllib3
    urllib3.disable_warnings()

    url = f"{settings.DMONEY_BASE_URL}/apiaccess/payment/gateway/payment/v1/token"
    headers = {
        "Content-Type": "application/json",
        "X-APP-Key": settings.DMONEY_X_APP_KEY
    }
    payload = {"appSecret": settings.DMONEY_APP_SECRET}

    resp = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)
    raw = resp.json()
    print(f"  Raw response: {raw}")

    # D-Money returns token directly with errorCode=None on success
    if raw.get("token") and raw.get("errorCode") is None:
        ok(f"Token received! {raw['token'][:28]}...")
        ok(f"Expires: {raw.get('expirationDate', 'unknown')}")
    else:
        fail(f"Token failed. errorCode={raw.get('errorCode')}, msg={raw.get('errorMsg')}")
except Exception as e:
    fail(f"Gateway error: {e}")


# ── 7. Network reachability ──────────────────────────────────────────────────
check("7. Network — D-Money server reachability")
try:
    import requests
    import urllib3
    urllib3.disable_warnings()
    url = settings.DMONEY_BASE_URL
    resp = requests.get(url, timeout=10, verify=False)
    ok(f"Server reachable. HTTP status: {resp.status_code}")
except requests.exceptions.ConnectionError:
    fail(f"Cannot reach {settings.DMONEY_BASE_URL}")
    print("  Check your internet connection or VPN")
except requests.exceptions.Timeout:
    fail("Connection timed out")
except Exception as e:
    warn(f"Reachability check: {e}")


# ── Summary ──────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print("  Done. Fix any [FAIL] items above before running the app.")
print('='*50 + "\n")
