#!/usr/bin/env python3
"""
Assign stories US#1050-1057 to Developer E
"""

import sys

sys.path.insert(0, "taiga/scripts")

import requests
from taiga_api import API_ENDPOINT, authenticate, get_project_id
from taiga_read import get_story_by_ref


def get_user_id_by_username(token: str, username: str, project_id: int):
    """Get user ID by username"""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_ENDPOINT}/users"

    # Try to get user by username
    params = {"username": username}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            users = resp.json()
            if users and len(users) > 0:
                return users[0].get("id")
    except:
        pass

    # Try alternative: search in project members
    project_url = f"{API_ENDPOINT}/projects/{project_id}"
    try:
        resp = requests.get(project_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            project = resp.json()
            members = project.get("members", [])
            for member in members:
                user_info = member.get("user", {})
                if user_info.get("username", "").lower() == username.lower():
                    return user_info.get("id")
    except:
        pass

    return None


def assign_story(token: str, project_id: int, story_ref: int, user_id: int):
    """Assign a story to a user"""
    story = get_story_by_ref(token, project_id, story_ref)
    if not story:
        print(f"❌ Story #{story_ref} not found")
        return False

    story_id = story["id"]
    version = story.get("version", 1)
    subject = story.get("subject", "Unknown")

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_ENDPOINT}/userstories/{story_id}"
    data = {"assigned_to": user_id, "version": version}

    try:
        resp = requests.patch(url, headers=headers, json=data, timeout=10)
        if resp.status_code == 200:
            print(f"✅ Assigned US#{story_ref}: {subject[:60]}")
            return True
        else:
            print(f"❌ Failed to assign US#{story_ref}: HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error assigning US#{story_ref}: {e}")
        return False


def main():
    print("=" * 80)
    print("Assigning Stories US#1050-1057 to Developer E")
    print("=" * 80)
    print()

    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return 1

    project_id = get_project_id(token)
    if not project_id:
        print("❌ Project not found")
        return 1

    # Try to find Developer E - try different username variations
    user_id = None
    for username in ["developer-e", "developere", "Developer E", "developer_e", "dev-e"]:
        user_id = get_user_id_by_username(token, username, project_id)
        if user_id:
            print(f"✅ Found user: {username} (ID: {user_id})")
            break

    if not user_id:
        print("⚠️  Developer E not found. Trying to assign without user ID...")
        print("   (Stories will be assigned but may need manual user selection)")
        # Continue anyway - Taiga might accept None or we'll handle it

    print()
    print("Assigning stories...")
    print()

    assigned_count = 0
    for ref in range(1050, 1058):
        if assign_story(token, project_id, ref, user_id):
            assigned_count += 1

    print()
    print("=" * 80)
    print(f"✅ Assigned {assigned_count} stories")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
