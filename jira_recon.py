import requests
import asyncio
import json
import os
import re
import sys

# ANSI escape codes for GREEN and reset colors
GREEN = "\033[92m"
RESET = "\033[0m"
CLEAR_SCREEN = "\033[2J\033[H"

# ASCII banner for "JIRA RECON"
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


async def filters(company):
    
    """ Retrieve different filters and then retrieve any available surnames """

    url = f"https://{company}.atlassian.net/rest/api/2/filter/search"

    response = requests.get(url)
    if response.status_code != 200:
        print(f"\nFailed to fetch filters. Status code: {response.status_code}")
        return

    data = response.json()

    os.makedirs(f"{company}_filters/", exist_ok=True)
    os.makedirs(f"{company}_filters/filter_names", exist_ok=True)
    
    os.makedirs(f"{company}_filters/usernames", exist_ok=True)

    with open(f"{company}_filters/{company}.json", "w") as f:
        json.dump(data, f, indent=4)
    print(f"\nFilters JSON saved to filters/{company}.json")

    def find_self_links(obj):
        self_links = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "self" and isinstance(value, str):
                    self_links.append(value)
                else:
                    self_links.extend(find_self_links(value))
        elif isinstance(obj, list):
            for item in obj:
                self_links.extend(find_self_links(item))
        return self_links

    self_urls = find_self_links(data)

    for link in self_urls:
        match = re.search(r"/(\d+)$", link)
        if match:
            id_number = match.group(1)
            try:
                res = requests.get(link)
                if res.status_code == 200:
                    json_data = res.json()

                    filename = f"{id_number}.json"
                    if "name" in json_data:
                        sanitized_name = re.sub(r'[^a-z0-9]+', '_', json_data["name"].lower()).strip('_')
                        filename = f"{sanitized_name}.json"

                    with open(f"{company}_filters/filter_names/{filename}", "w") as f:
                        json.dump(json_data, f, indent=4)

                    print(f"[✓] Saved: filters/filter_names/{GREEN}{filename}{RESET}")
                else:
                    print(f"Failed to fetch {link} (Status {res.status_code})")
            except Exception as e:
                print(f"Error fetching {link}: {e}")
        # else:
            # print(f"⏭️ Skipped link (no numeric ID): {link}")

        os.makedirs(f"{company}_filters/usernames", exist_ok=True)
        all_users = []
        seen_ids = set()
        seen_names = set()

        for file in os.listdir(f"{company}_filters/filter_names"):
            if file.endswith(".json"):
                try:
                    with open(f"{company}_filters/filter_names/{file}", "r") as f:
                        data = json.load(f)
                        for permission in data.get("editPermissions", []):
                            user = permission.get("user", {})
                            displayName = user.get("displayName")
                            active = user.get("active")
                            accountId = user.get("accountId")

                            if displayName and accountId:
                                if accountId not in seen_ids and displayName not in seen_names:
                                    all_users.append({
                                        "displayName": displayName,
                                        "active": active,
                                        "accountId": accountId
                                    })
                                    seen_ids.add(accountId)
                                    seen_names.add(displayName)
                except Exception as e:
                    print(f"Error processing {file}: {e}")
        with open(f"{company}_filters/usernames/filter_usernames.json", "w") as f:
            json.dump(all_users, f, indent=4)

async def dashboard(company):
    
    """ Retrieve different dashboars and then retrieve any available surnames"""
    
    url = f"https://{company}.atlassian.net/rest/api/3/dashboard"

    response = requests.get(url)
    if response.status_code != 200:
        print(f"\nFailed to fetch dashboard. Status code: {response.status_code}")
        return

    data = response.json()

    os.makedirs(f"{company}_dashboard", exist_ok=True)
    with open(f"{company}_dashboard/{company}.json", "w") as f:
        json.dump(data, f, indent=4)
    print(f"\nRaw dashboard JSON saved to dashboard/{company}.json")

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

    unique_users = []
    seen_ids = set()
    seen_names = set()

    for user in user_info_raw:
        accountId = user.get("accountId")
        displayName = user.get("displayName")

        if accountId and displayName:
            if accountId not in seen_ids and displayName not in seen_names:
                unique_users.append(user)
                seen_ids.add(accountId)
                seen_names.add(displayName)

    with open(f"{company}_dashboard/{company}_users.json", "w") as f:
        json.dump(unique_users, f, indent=4)
    print(f"Extracted user info saved to dashboard/{company}_users.json")


    def find_self_links(obj):
        self_links = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "self" and isinstance(value, str):
                    self_links.append(value)
                else:
                    self_links.extend(find_self_links(value))
        elif isinstance(obj, list):
            for item in obj:
                self_links.extend(find_self_links(item))
        return self_links

    self_urls = find_self_links(data)

    os.makedirs(f"{company}_dashboard/dashboard", exist_ok=True)
    for link in self_urls:
        match = re.search(r"/(\d+)$", link)
        if match:
            id_number = match.group(1)
            try:
                res = requests.get(link)
                if res.status_code == 200:
                    with open(f"{company}_dashboard/dashboard/{id_number}.json", "w") as f:
                        json.dump(res.json(), f, indent=4)
                    print(f"[✓] Saved: {company}_dashboard/dashboard/{GREEN}{id_number}.json{RESET}")
                else:
                    print(f"Failed to fetch {link} (Status {res.status_code})")
            except Exception as e:
                print(f"❌ Error fetching {link}: {e}")
        # else:
        #     print(f"⏭️ Skipped link (no numeric ID): {link}")


def print_filters_statistics(company):
    filters_dir = f"{company}_filters"
    filter_names_dir = os.path.join(filters_dir, "filter_names")
    usernames_file = os.path.join(filters_dir, "usernames", "filter_usernames.json")

    filter_count = 0
    username_count = 0

    if os.path.exists(filter_names_dir):
        filter_count = len([f for f in os.listdir(filter_names_dir) if f.endswith('.json')])
    else:
        print(f"Directory {filter_names_dir} not found.")

    if os.path.exists(usernames_file):
        try:
            with open(usernames_file, 'r') as f:
                usernames_data = json.load(f)
                username_count = len(usernames_data) 
        except Exception as e:
            print(f"Error reading usernames file: {e}")
    else:
        print(f"Usernames file {usernames_file} not found.")

    print(f"\n{GREEN}Statistics:{RESET}")
    print(f"Filters Found: {filter_count}")
    print(f"Usernames Extracted: {username_count}")

def print_dashboard_statistics(company):
    dashboard_dir = f"{company}_dashboard/dashboard/"
    dashboard_users_file = f"{company}_dashboard/{company}_users.json"

    dashboard_count = 0
    username_count = 0

    if os.path.exists(dashboard_dir):
        dashboard_count = len([f for f in os.listdir(dashboard_dir) if f.endswith('.json') and f != f"{company}.json"])
    else:
        print(f"Directory {dashboard_dir} not found.")

    if os.path.exists(dashboard_users_file):
        try:
            with open(dashboard_users_file, 'r') as f:
                usernames_data = json.load(f)
                username_count = len(usernames_data)
        except Exception as e:
            print(f"Error reading users file: {e}")
    else:
        print(f"Dashboard users file {dashboard_users_file} not found.")

    print(f"\n{GREEN}Dashboard Statistics:{RESET}")
    print(f"Dashboard Files Found: {dashboard_count}")
    print(f"Usernames Extracted: {username_count}")


if __name__ == "__main__":
    print(CLEAR_SCREEN, end="")
    print(BANNER)

    company_name = input("Enter company name: ").strip()

    print("\nWhat do you want to test?")
    print("1. Filters")
    print("2. Dashboard")
    print("3. Both")

    choice = input("Enter choice (1/2/3): ").strip()

    async def main():
        if choice not in ("1", "2", "3"):
            print(f"\n{GREEN}Invalid choice. Please enter 1, 2, or 3.{RESET}")
            return

        tasks = []
        flags = []

        if choice == "1":
            done_flag = [False]
            flags.append(done_flag)
            tasks.append(asyncio.create_task(filters(company_name)))
            spinner_task = asyncio.create_task(spinner("Filters", done_flag))
            await asyncio.gather(tasks[0])
            done_flag[0] = True
            await spinner_task
            print_filters_statistics(company_name)

        elif choice == "2":
            done_flag = [False]
            flags.append(done_flag)
            tasks.append(asyncio.create_task(dashboard(company_name)))
            spinner_task = asyncio.create_task(spinner("Dashboard", done_flag))
            await asyncio.gather(tasks[0])
            done_flag[0] = True
            await spinner_task
            print_dashboard_statistics(company_name)

        elif choice == "3":
            done_flag1 = [False]
            done_flag2 = [False]
            flags.extend([done_flag1, done_flag2])
            task_filters = asyncio.create_task(filters(company_name))
            task_dashboard = asyncio.create_task(dashboard(company_name))
            spinner_filters = asyncio.create_task(spinner("Filters", done_flag1))
            spinner_dashboard = asyncio.create_task(spinner("Dashboard", done_flag2))

            await asyncio.gather(task_filters, task_dashboard)

            done_flag1[0] = True
            done_flag2[0] = True

            await asyncio.gather(spinner_filters, spinner_dashboard)
            print_filters_statistics(company_name)
            print_dashboard_statistics(company_name)

    asyncio.run(main())
