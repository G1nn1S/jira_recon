import requests
import asyncio
import aiohttp
import aiofiles
import json
import os
import re
import sys
import shutil  # for terminal width

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
CLEAR_SCREEN = "\033[2J\033[H"

BANNER = f"""
{GREEN}
       █████ █████ ███████████     █████████      ███████████   ██████████   █████████     ███████    ██████   █████
      ░░███ ░░███ ░░███░░░░░███   ███░░░░░███    ░░███░░░░░███ ░░███░░░░░█  ███░░░░░███  ███░░░░░███ ░░██████ ░░███ 
       ░███  ░███  ░███    ░███  ░███    ░███     ░███    ░███  ░███  █ ░  ███     ░░░  ███     ░░███ ░███░███ ░███ 
       ░███  ░███  ░██████████   ░███████████     ░██████████   ░██████   ░███         ░███      ░███ ░███░░███░███ 
       ░███  ░███  ░███░░░░░███  ░███░░░░░███     ░███░░░░░███  ░███░░█   ░███         ░███      ░███ ░███ ░░██████ 
 ███   ░███  ░███  ░███    ░███  ░███    ░███     ░███    ░███  ░███ ░   █░░███     ███░░███     ███  ░███  ░░█████ 
░░████████   █████ █████   █████ █████   █████    █████   █████ ██████████ ░░█████████  ░░░███████░   █████  ░░█████
 ░░░░░░░░   ░░░░░ ░░░░░   ░░░░░ ░░░░░   ░░░░░    ░░░░░   ░░░░░ ░░░░░░░░░░   ░░░░░░░░░     ░░░░░░░    ░░░░░    ░░░░░ 
                                                                                                                    
{RESET}
"""

SPINNER_FRAMES = ["|", "/", "-", "\\"]

collected_users = []
seen_account_ids = set()
seen_display_names = set()


async def spinner(task_name, done_flag):
    idx = 0
    while not done_flag[0]:
        sys.stdout.write(
            f"\r{GREEN}[{SPINNER_FRAMES[idx % len(SPINNER_FRAMES)]}] {task_name} running...{RESET} "
        )
        sys.stdout.flush()
        idx += 1
        await asyncio.sleep(0.1)
    sys.stdout.write(f"\r{GREEN}[✔] {task_name} completed!{' ' * 20}{RESET}\n")


async def find_self_links(obj):
    self_links = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "self" and isinstance(value, str):
                self_links.append(value)
            else:
                self_links.extend(await find_self_links(value))
    elif isinstance(obj, list):
        for item in obj:
            self_links.extend(await find_self_links(item))
    return self_links


async def fetch_json(session, url):
    try:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"❌ Failed to fetch {url}. Status: {response.status}")
                return None
            return await response.json()
    except Exception as e:
        print(f"⚠️ Exception fetching {url}: {e}")
        return None


async def fetch_and_save_filter(session, url, company):
    match = re.search(r"/(\d+)$", url)
    if not match:
        return None 

    data = await fetch_json(session, url)
    if not data:
        return None

    id_number = match.group(1)
    filename = f"{id_number}.json"
    if "name" in data:
        sanitized = re.sub(r'[^a-z0-9]+', '_', data["name"].lower()).strip('_')
        filename = f"{sanitized}.json"

    path = f"{company}_filters/filter_names/{filename}"
    async with aiofiles.open(path, "w") as f:
        await f.write(json.dumps(data, indent=4))
    print(f"[✓] Saved: filter_names/{filename}")

    collect_users_from_filter(data)

    return data


def collect_users_from_filter(data):
    global collected_users, seen_account_ids, seen_display_names
    for permission in data.get("editPermissions", []):
        user = permission.get("user", {})
        displayName = user.get("displayName")
        accountId = user.get("accountId")
        active = user.get("active")

        if displayName and accountId:
            if accountId not in seen_account_ids and displayName not in seen_display_names:
                collected_users.append({
                    "displayName": displayName,
                    "active": active,
                    "accountId": accountId
                })
                seen_account_ids.add(accountId)
                seen_display_names.add(displayName)


async def filters(company):
    os.makedirs(f"{company}_filters/filter_names", exist_ok=True)
    os.makedirs(f"{company}_filters/usernames", exist_ok=True)

    base_url = f"https://{company}.atlassian.net/rest/api/2/filter/search"

    async with aiohttp.ClientSession() as session:
        root_data = await fetch_json(session, base_url)
        if not root_data:
            print("❌ Failed to fetch base filters.")
            return

        async with aiofiles.open(f"{company}_filters/{company}.json", "w") as f:
            await f.write(json.dumps(root_data, indent=4))

        print(f"\n📦 Saved root filter list to {company}_filters/{company}.json")

        self_urls = await find_self_links(root_data)

        tasks = [
            asyncio.create_task(fetch_and_save_filter(session, url, company))
            for url in self_urls
        ]
        await asyncio.gather(*tasks)


async def dashboard(company):
    """ Retrieve different dashboards and then retrieve any available usernames """

    base_url = f"https://{company}.atlassian.net/rest/api/3/dashboard"

    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, base_url)
        if not data:
            print("❌ Failed to fetch dashboard data.")
            return

        os.makedirs(f"{company}_dashboard", exist_ok=True)
        async with aiofiles.open(f"{company}_dashboard/{company}.json", "w") as f:
            await f.write(json.dumps(data, indent=4))
        print(f"\nRaw dashboard JSON saved to {company}_dashboard/{company}.json")

        def extract_user_info(obj):
            users = []
            if isinstance(obj, dict):
                if all(k in obj for k in ("displayName", "active", "accountId")):
                    users.append(
                        {
                            "displayName": obj["displayName"],
                            "active": obj["active"],
                            "accountId": obj["accountId"],
                        }
                    )
                for value in obj.values():
                    users.extend(extract_user_info(value))
            elif isinstance(obj, list):
                for item in obj:
                    users.extend(extract_user_info(item))
            return users

        user_info_raw = extract_user_info(data)

        global collected_users, seen_account_ids, seen_display_names

        for user in user_info_raw:
            accountId = user.get("accountId")
            displayName = user.get("displayName")

            if accountId and displayName:
                if accountId not in seen_account_ids and displayName not in seen_display_names:
                    collected_users.append(user)
                    seen_account_ids.add(accountId)
                    seen_display_names.add(displayName)

        async with aiofiles.open(f"{company}_dashboard/{company}_users.json", "w") as f:
            await f.write(json.dumps(user_info_raw, indent=4))
        print(f"\n✅ Saved unique dashboard users to {company}_dashboard/{company}_users.json")

        print(f"\n📊 Dashboard URLs processed: 1")
        print(f"👤 Unique users extracted (dashboard): {len(user_info_raw)}\n")


def pretty_print_users(users):
    if not users:
        print("No users found.")
        return

    term_width = shutil.get_terminal_size((80, 20)).columns
    col1_width = 25 
    col2_width = 8  
    col3_width = term_width - col1_width - col2_width - 10

    print(f"\n{GREEN}=== All Unique Usernames Found ==={RESET}\n")
    header = f"{'Display Name':<{col1_width}}  {'Active':<{col2_width}}  {'Account ID':<{col3_width}}"
    print(header)
    print("-" * len(header))

    for user in users:
        name = user['displayName'][:col1_width-1]
        active = user['active']
        active_str = f"{GREEN}Yes{RESET}" if active else f"{RED}No{RESET}"
        account_id = user['accountId']
        if len(account_id) > col3_width:
            account_id = account_id[:col3_width-3] + "..."
        print(f"{name:<{col1_width}}  {active_str:<{col2_width}}  {account_id:<{col3_width}}")

    print("\n")


async def main():
    print(CLEAR_SCREEN)
    print(BANNER)
    company = input("Enter the Atlassian company name (subdomain): ").strip()

    done_flag_filters = [False]
    done_flag_dashboard = [False]

    spinner_task_filters = asyncio.create_task(spinner("Filters", done_flag_filters))
    spinner_task_dashboard = asyncio.create_task(spinner("Dashboard", done_flag_dashboard))

    filters_task = asyncio.create_task(filters(company))
    dashboard_task = asyncio.create_task(dashboard(company))

    await filters_task
    done_flag_filters[0] = True

    await dashboard_task
    done_flag_dashboard[0] = True

    await spinner_task_filters
    await spinner_task_dashboard

    pretty_print_users(collected_users)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
