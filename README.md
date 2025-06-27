# JIRA Recon Tool

**JIRA Recon** is an asynchronous Python tool designed to scrape and collect information from public JIRA instances. It extracts filters, dashboards, and user-related metadata such as `displayName`, `active` status, and `accountId`. The results are saved in structured JSON files for analysis and recon purposes.

## Features

- Collects filters and dashboards from a JIRA instance
- Extracts usernames and account info
- Automatically saves results in organized directories
- Includes animated terminal output with spinners and banners

## Usage

1. Clone the repository:
    ```bash
    git clone https://github.com/your-repo/jira-recon.git
    cd jira_recon
    ```

2. Install dependencies:
    ```bash
    pip3 install -r requirements.txt
    ```

3. Run the tool:
    ```bash
    python3 main.py
    ```

4. Enter the target JIRA domain (e.g., `example` for `https://example.atlassian.net`) and choose what to scrape (filters, dashboards, or both).
