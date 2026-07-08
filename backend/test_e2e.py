"""Full end-to-end test: login -> upload PDF -> ask question.

Usage:
    Set the following environment variables before running:
        TEST_EMAIL=your-test-email@example.com
        TEST_PASSWORD=your-test-password
        BACKEND=http://localhost:5000

    Then run:
        python test_e2e.py
"""
import os
import requests

BACKEND = os.getenv("BACKEND", "http://localhost:5000")
TEST_EMAIL = os.getenv("TEST_EMAIL")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")

if not TEST_EMAIL or not TEST_PASSWORD:
    print("ERROR: Set TEST_EMAIL and TEST_PASSWORD environment variables before running.")
    exit(1)

# Step 1: Login via StudyBuddy backend
print("=== Step 1: Login ===")
resp = requests.post(
    f"{BACKEND}/auth/login",
    headers={"Content-Type": "application/json"},
    json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
)
print("Status:", resp.status_code)
if resp.status_code != 200:
    print("FAILED:", resp.text)
    exit(1)
token = resp.json()["access_token"]
print("Token OK:", token[:50], "...")
headers_auth = {"Authorization": f"Bearer {token}"}

# Step 2: Upload
print()
print("=== Step 2: Upload PDF ===")
with open("test_upload.pdf", "rb") as f:
    up = requests.post(
        f"{BACKEND}/upload",
        headers=headers_auth,
        files={"pdf": ("test_upload.pdf", f, "application/pdf")},
    )
print("Status:", up.status_code)
print("Response:", up.json())

if up.status_code != 200:
    print("UPLOAD FAILED - stopping here.")
    exit(1)

# Step 3: Ask question
print()
print("=== Step 3: Ask Question ===")
ask = requests.post(
    f"{BACKEND}/ask",
    headers={**headers_auth, "Content-Type": "application/json"},
    json={"query": "Who created Python and when?"},
)
print("Status:", ask.status_code)
data = ask.json()
print("Answer:", data.get("answer", "N/A"))
print("Sources:", data.get("sources", []))
print()
print("=== ALL TESTS PASSED! ===")
