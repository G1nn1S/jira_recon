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
    git clone https://github.com/G1nn1S/jira-recon.git
    cd jira_recon
    ```

2. Install dependencies:
    ```bash
    pip3 install -r requirements.txt
    ```

3. Run the tool:
    ```bash
    python3 jira_recon.py
    ```

4. Enter the target JIRA domain (e.g., `example` for `https://example.atlassian.net`) and choose what to scrape (filters, dashboards, or both).

## ⚠️ Disclaimer

This tool is developed **strictly for educational, ethical hacking, and authorized security testing purposes**. You **must** obtain proper permission before using it on any JIRA instance that you do not own or have explicit authorization to assess.

**Unauthorized use of this tool against systems you do not own is illegal and unethical. The authors take no responsibility for any misuse or damage caused by this tool.**

Use responsibly — always hack with permission. 🛡️

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
