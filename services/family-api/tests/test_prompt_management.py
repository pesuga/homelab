import requests
import json
import sys

BASE_URL = "http://localhost:8001"  # Using 8001 as per settings.py

def test_prompt_management():
    print("Testing Prompt Management API...")

    # 1. List Roles
    print("\n1. Listing Roles...")
    try:
        response = requests.get(f"{BASE_URL}/api/phase2/prompts/roles")
        if response.status_code == 200:
            print(f"✅ Success: {response.json()}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 2. List Skills
    print("\n2. Listing Skills...")
    try:
        response = requests.get(f"{BASE_URL}/api/phase2/prompts/skills")
        if response.status_code == 200:
            print(f"✅ Success: {response.json()}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 3. Get Core Prompt
    print("\n3. Getting Core Prompt...")
    original_core_prompt = ""
    try:
        response = requests.get(f"{BASE_URL}/api/phase2/prompts/core")
        if response.status_code == 200:
            data = response.json()
            original_core_prompt = data.get("prompt", "")
            print(f"✅ Success: Length {data.get('length')}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    # 4. Update Core Prompt
    print("\n4. Updating Core Prompt...")
    new_content = original_core_prompt + "\n\n# TEST UPDATE\nThis is a test update."
    try:
        response = requests.put(
            f"{BASE_URL}/api/phase2/prompts/core",
            json={"content": new_content}
        )
        if response.status_code == 200:
            print(f"✅ Success: {response.json()}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 5. Verify Update
    print("\n5. Verifying Update...")
    try:
        response = requests.get(f"{BASE_URL}/api/phase2/prompts/core")
        if response.status_code == 200:
            data = response.json()
            if "# TEST UPDATE" in data.get("prompt", ""):
                print("✅ Success: Update verified")
            else:
                print("❌ Failed: Update not found in content")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # 6. Restore Core Prompt
    print("\n6. Restoring Core Prompt...")
    try:
        response = requests.put(
            f"{BASE_URL}/api/phase2/prompts/core",
            json={"content": original_core_prompt}
        )
        if response.status_code == 200:
            print(f"✅ Success: {response.json()}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_prompt_management()
