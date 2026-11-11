"""Workstreams, phases, exit criteria and tasks from the
"Yantralive CTO Office: Technology & IT Organization Plan" (11 Nov 2026)."""

WORKSTREAMS = [
    ("inventory", "Inventory and governance",
     "Know every asset, system, account, vendor and repo, and who decides what."),
    ("security", "Security",
     "Stop the common attacks: phishing, stolen passwords, ransomware, leaked keys."),
    ("ip", "IP protection and data theft",
     "Make sure the company, not individuals, owns and controls code, data and know-how. "
     "Data-theft prevention is priority one."),
    ("architecture", "Architecture and scale",
     "Standards, environments, automation and observability so growth does not break things."),
    ("vendors", "Vendors, policy and people",
     "SaaS spend, written policies, and the team to run it all."),
]

# key, name, subtitle, days from programme start, exit criteria
PHASES = [
    ("d30", "Days 1–30", "See it and stop the bleeding", 30, [
        "Full inventory exists",
        "MFA is on everywhere",
        "No company asset is owned by a personal account",
    ]),
    ("d60", "Days 31–60", "Control and standardise", 60, [
        "Every laptop managed",
        "Every SaaS tool behind SSO or scheduled for it",
        "Leaver process tested",
    ]),
    ("d90", "Days 61–90", "Build for scale and prove it works", 90, [
        "DR tested",
        "CI/CD with security checks on all main services",
        "First quarterly access review done",
    ]),
]

# phase, workstream, priority, title, description
TASKS = [
    # ---- Days 1–30 ----
    ("d30", "inventory", "high",
     "Publish the CTO office charter and decision-rights table; name the new team lead as "
     "part-time IT owner", ""),
    ("d30", "inventory", "high",
     "Build the source-of-truth inventory register",
     "One shared sheet covering people and access, devices, cloud, code, data, domains/DNS/email, "
     "SaaS and vendors, contracts and IP. Each row: owner, admin account, criticality "
     "(High/Medium/Low), company-owned yes/no. Export user lists, pull 12 months of card and bank "
     "statements, and interview each team lead for 15 minutes."),
    ("d30", "ip", "high",
     "Map where prospect, customer, inventory and vendor-price data lives and who can read and "
     "export it", ""),
    ("d30", "ip", "high",
     "In the app: remove any export-all, paginate and rate-limit list pages, scope users to their "
     "own leads; only 2–3 named people can bulk export",
     "Enforce in the FastAPI API, not just by hiding UI buttons. ~50 rows per page."),
    ("d30", "ip", "high",
     "Find old prospect Excel sheets and lock them down",
     "Search Drive (admin console), Gmail attachments and laptops. Move them into one restricted "
     "shared drive or delete them, and ask staff to confirm they deleted local copies."),
    ("d30", "security", "high",
     "Google Workspace: enforce 2-Step Verification, block external Drive sharing by default, "
     "disable Gmail auto-forwarding, turn on bulk-download alerts", ""),
    ("d30", "security", "high",
     "Enforce MFA on AWS and GitLab; move AWS to IAM Identity Center with SSO from Google; lock "
     "the AWS root account", ""),
    ("d30", "inventory", "high",
     "Move any personally-owned domain, repo, AWS account or SaaS admin into company ownership",
     ""),
    ("d30", "ip", "high",
     "Disable accounts of everyone who has left; remove unused admin rights", ""),
    ("d30", "ip", "medium",
     "Contractors: own company Google account with an end date, only the repos they need, no "
     "production or prospect data",
     "8 contractors. Each needs a signed contract with confidentiality, IP assignment and data "
     "return. Review contractor access monthly."),
    ("d30", "security", "medium", "Roll out Bitwarden company-wide", ""),
    ("d30", "ip", "medium",
     "GitLab: protected branches, Gitleaks secret scanning in CI; rotate any exposed secrets", ""),
    ("d30", "security", "medium", "Set SPF, DKIM and DMARC on the company domain", ""),
    ("d30", "architecture", "medium",
     "Confirm AWS backups exist for production databases and test one restore", ""),
    ("d30", "ip", "high",
     "Lawyer reviews employment and contractor agreements for confidentiality, IP assignment and "
     "data return; list gaps", "Clauses must be enforceable in India."),
    ("d30", "inventory", "medium",
     "Start the risk register with the top 10 risks, data theft first",
     "Columns: risk, likelihood (1–5), impact (1–5), score, owner, mitigation, due date, status."),
    # ---- Days 31–60 ----
    ("d60", "security", "high",
     "Company laptops for everyone who sees customer data; restrict the app to office network or "
     "VPN; enroll in Google endpoint management; block USB storage and personal cloud sync",
     "VPN options: WireGuard, or Headscale with Tailscale clients."),
    ("d60", "security", "medium",
     "Deploy Wazuh agents to laptops and servers; enforce disk encryption and auto-updates", ""),
    ("d60", "ip", "high",
     "Add export logging to the admin panel and FastAPI list endpoints; keep logs at least 1 year",
     "Log user, time, IP and rows returned. Alert when someone pulls far more than usual, "
     "especially after hours or during a notice period."),
    ("d60", "ip", "high", "Plant canary records in prospect and vendor-price data",
     "Fake but realistic prospects and vendor prices, unique per team or person."),
    ("d60", "vendors", "medium",
     "Put the top SaaS tools behind Google SSO; cancel unused and duplicate tools", ""),
    ("d60", "vendors", "high",
     "Write and roll out the first five policies (acceptable use, access control, "
     "joiner/mover/leaver, data handling, incident response)", ""),
    ("d60", "ip", "high",
     "Implement the leaver checklist with HR, including cutting bulk-data access on resignation, "
     "and test it on the next leaver",
     "Review the leaver's last 30 days of downloads and shares; disable accounts on the last day; "
     "collect laptops; written confidentiality reminder."),
    ("d60", "ip", "high",
     "Get updated confidentiality, IP-assignment and NDA agreements signed by all 30 staff and "
     "contractors", ""),
    ("d60", "architecture", "medium",
     "Separate dev, staging and production AWS accounts; lock down production and database access",
     "Production DB access only for 1–2 engineers through AWS IAM, with queries logged."),
    ("d60", "security", "medium", "Turn on CloudTrail, GuardDuty and billing alerts", ""),
    ("d60", "architecture", "medium",
     "Draw the current architecture map and list single points of failure", ""),
    ("d60", "security", "medium",
     "Run a 20-minute security and data-handling session for all staff", ""),
    # ---- Days 61–90 ----
    ("d90", "architecture", "medium",
     "OpenTofu/Terraform for production AWS; GitLab CI with tests, Semgrep, Trivy and Gitleaks", ""),
    ("d90", "architecture", "medium",
     "Prometheus, Grafana and Uptime Kuma with alerts to an on-call person", ""),
    ("d90", "architecture", "high", "Disaster-recovery test against agreed RTO/RPO", ""),
    ("d90", "ip", "high",
     "First quarterly access review, starting with who can see and export customer and pricing "
     "data", ""),
    ("d90", "security", "medium",
     "Incident-response tabletop: \"a salesperson resigns and emails the prospect list to a "
     "competitor\"", ""),
    ("d90", "vendors", "medium",
     "Remaining policies (secure development, vendor, backup/DR, open source, BYOD, privacy)", ""),
    ("d90", "vendors", "medium",
     "Vendor review: data-processing terms and renewal calendar for critical vendors", ""),
    ("d90", "architecture", "low", "Cost tagging and first monthly AWS cost review", ""),
    ("d90", "vendors", "medium",
     "Decide on upgrading Google Workspace from Business Standard to Business Plus (Vault, laptop "
     "wipe)", ""),
    ("d90", "inventory", "medium",
     "Present the 12-month technology roadmap and budget to the CEO", ""),
]
