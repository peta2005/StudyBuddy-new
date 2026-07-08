"""Diagnostic tool for JWT clock skew analysis.

Usage:
    Set environment variables before running:
        TEST_EMAIL=your-test-email@example.com
        TEST_PASSWORD=your-test-password
        BACKEND=http://localhost:5000

    Then run:
        python diag_skew.py
"""
import time
import os
import requests
import jwt
from jwt.algorithms import ECAlgorithm
from dotenv import load_dotenv

load_dotenv(".env")

BACKEND = os.getenv("BACKEND", "http://localhost:5000")
TEST_EMAIL = os.getenv("TEST_EMAIL")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")

if not TEST_EMAIL or not TEST_PASSWORD:
    print("ERROR: Set TEST_EMAIL and TEST_PASSWORD environment variables before running.")
    exit(1)

# Login via StudyBuddy backend
print("Logging in...")
resp = requests.post(
    f"{BACKEND}/auth/login",
    headers={"Content-Type": "application/json"},
    json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
)
print("Login status:", resp.status_code)
if resp.status_code != 200:
    print("Login failed:", resp.text)
    exit(1)
token = resp.json()["access_token"]

# Decode without verification
header = jwt.get_unverified_header(token)
claims = jwt.decode(token, options={"verify_signature": False})

local_now = int(time.time())
token_iat = claims["iat"]
token_exp = claims["exp"]

print()
print("=== Clock Analysis ===")
print("Local time (unix):", local_now)
print("Token iat  (unix):", token_iat)
print("Token exp  (unix):", token_exp)
skew = token_iat - local_now
print()
print(f"Clock skew: {skew} seconds")
if skew > 0:
    print(f"  => Your clock is {skew}s BEHIND the server")
    if skew <= 60:
        print(f"  => leeway=60 should be ENOUGH to cover this")
    else:
        print(f"  => leeway=60 is NOT ENOUGH, need at least leeway={skew + 5}")
else:
    print(f"  => Clock is fine (ahead by {abs(skew)}s)")

print()
print("=== Token Header ===")
print("alg:", header.get("alg"))
print("kid:", header.get("kid"))
