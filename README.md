# CommandScout: Tactical Syntax & Command Scaffolding Studio v2.0

**Assistive Universal Design, Cognitive Scaffolding & Hardened Execution for Cyber Operations**  
*Engineered by Austin Davis (U.S. Army Veteran 19D Cav Scout / DeVry University Cyber Security Student)*

---

## 🎯 Operational Overview

**CommandScout** is a high-speed, offline-first command scaffolding studio, syntax builder, and hardened execution runner. It was purpose-built to solve three critical operational challenges:
1. **Physical Ergonomics & Zero-Typing**: Designed specifically for operators with severe motor/hand injuries to eliminate tedious, error-prone manual typing of complex security syntax, flags, and delimiters.
2. **Cognitive Scaffolding for ADHD**: Mitigates working memory exhaustion and syntax frustration by transforming command-line parameters (IPs, Ports, BSSIDs, Interfaces, Wordlists) into visual input badges with live dynamic syntax previews.
3. **Deliberate Execution Safety Model**: Replaces unrestricted arbitrary shell execution with a multi-tiered safety model: copy-only as the primary default action, explicit confirmation gates, structured argument validation, distinct environment runners (`wsl`, `powershell`, `adb`), and immutable audit logging.

---

## 🛡️ Hardened Architecture & Security Model

### 1. Deliberate Execution Safety Model
* **Copy-First Philosophy**: The prominent default action on every recipe card is **1-Click Copy** with instantaneous system clipboard injection and audio feedback.
* **Safety Confirmation Gate**: Direct execution requires passing through a modal confirmation gate that displays:
  * Target environment runner badge (`WSL2 Kali Linux`, `Windows PowerShell 7`, or `Android ADB`).
  * Full rendered command preview.
  * Risk analysis banner highlighting elevated privileges (`sudo`), disk wiping (`format`, `dd`), or process termination (`kill`, `pkill`).
* **Trusted Local Mode Toggle**: Optional server switch (`/api/settings`) allowing power users to bypass confirmation during high-tempo lab engagements, backed by a persistent visual status indicator.
* **Audit Trail Logging**: Every execution event is appended to [`audit_log.jsonl`](audit_log.jsonl) with UTC timestamp, client IP, environment, rendered command, confirmation status, exit code, and execution duration in milliseconds.

### 2. Environment-Specific Execution Engines
* **Linux & Kali Security**: Routed natively via `wsl.exe bash -c <command>`.
* **Windows & PowerShell**: Prioritizes modern PowerShell 7 (`pwsh.exe`) with transparent fallback to Windows PowerShell (`powershell.exe`).
* **Android & Mobile Forensics**: Routed distinctly through Android Debug Bridge (`adb.exe`), resolving device-level shell commands (`adb shell ...`) and host-side bridge directives (`adb ...`) cleanly without PowerShell mislabeling.

### 3. Versioned Database Contract & Schema Validation
* **Strict Startup Contract (`validate_catalog`)**: The backend enforces JSON schema compliance at launch. Every tool must have valid `id`, `name`, `category`, and non-empty `recipes`. Every recipe template must strictly match declared parameter keys, completely eliminating silent UI breakages.
* **Hardware Sensors & Telemetry Model ([`sensors.json`](sensors.json))**: Centralizes live hardware targets and sensor parameters:
  * **SDR Signals Intelligence**: Nooelec NESDR SMArt v5 frequencies (1090 MHz ADS-B, 137.1/137.9 MHz NOAA/Meteor, 145.8 MHz ISS Voice) and sample rates.
  * **Tactical Wi-Fi**: Qualcomm Atheros AR9271 interface mappings (`wlan0` managed / `wlan1mon` monitor).
  * **Android Targets**: Samsung Galaxy S24 FE and Revoview AS65U ADB endpoints.

### 4. Resilient & Hardened Application Shell
* **Threaded HTTP Server**: Built on Python's `ThreadingHTTPServer` to prevent long-running commands from blocking concurrent requests or UI rendering.
* **Cross-Platform Hardening**: Platform capability checks guard Windows-specific modules (`winsound`, `clip.exe`), falling back gracefully to cross-platform clipboards (`pbcopy`, `xclip`, `wl-copy`) and terminal chimes.
* **Safer DOM Construction**: Replaced raw `innerHTML` interpolations with safe DOM node creation and text escaping, eliminating XSS risks.
* **Portable Launcher ([`Launch_CommandScout.bat`](Launch_CommandScout.bat))**: Dynamically detects Miniconda, system Python, or `py.exe` without hardcoded path dependencies.

---

## 🗃️ 111-Tool / 417-Recipe Tactical Arsenal (`commands_db.json`)

* **Linux & Kali Security (65 Tools / 222 Recipes)**:
  * Network Reconnaissance & Port Scanning (Nmap, Masscan, Rustscan, Zmap)
  * Wireless & RF Auditing (Aircrack-ng, Kismet, hcxdumptool, Reaver, Bully, Wifite)
  * Web Application & API Pentesting (Gobuster, Feroxbuster, Nikto, Sqlmap, Ffuf, Wpscan)
  * Password Recovery & Hash Cracking (Hashcat, John the Ripper, Hydra, Medusa)
  * Exploitation & Post-Exploitation (Metasploit, Msfvenom, Searchsploit, Chisel, Socat)
  * Forensics, Traffic Analysis & DFIR (Wireshark, Tshark, Volatility, Foremost, Binwalk, Exiftool)
  * Privilege Escalation & Audit (LinPEAS, Sudo LPE Hunter, SUID Finder, Capability Audits)

* **Windows & PowerShell (34 Tools / 112 Recipes)**:
  * DFIR & Event Log Forensics (Security Event IDs 4625, 4624, 4688, Defender exclusions)
  * Persistence & Autostart Hunting (Run/RunOnce, Scheduled Tasks, WMI Event Consumers)
  * Active Directory Reconnaissance (ADSI .NET LDAP zero-footprint domain queries)
  * Host Hardening & Telemetry (LSASS RunAsPPL, Firewall profiles, Controlled Folder Access)
  * System Administration & Hardware Diagnostics (Winget, Sysinternals, DISM/SFC, Battery Telemetry)

* **Android & Mobile Forensics (12 Tools / 83 Recipes)**:
  * ADB Device Management & Wireless Pairing (Pairing, Multi-device targeting, State triage)
  * Package & Application Auditing (Package enumeration, APK extraction, Permissions analysis)
  * Logcat & Real-time Telemetry (Crash monitoring, Filtered tag capture, Buffer management)
  * File System & Storage Triage (Pull/push forensics, SD card triage, Partition dumps)
  * Activity Manager & Intent Injection (Start activities, Send broadcast intents, Deep links)
  * Battery, Power & Thermal Telemetry (`dumpsys battery`, Unplug simulation, Thermals)

---

## 🧪 Automated Verification & Regression Testing

CommandScout includes a comprehensive automated test suite ([`test_command_scout.py`](test_command_scout.py)) verifying schema integrity, safety enforcement, and runner routing:

```bash
python test_command_scout.py
```

* **Test Suite Validates**:
  * Strict schema compliance across all 111 tools and 417 recipes.
  * Template placeholder integrity (ensuring 0 orphaned parameters).
  * Hardware sensors registry structure and valid target parameters.
  * Environment runner resolution (`wsl`, `powershell`, `adb`).
  * Safety Gate enforcement (unconfirmed execution rejected with HTTP 403 `CONFIRMATION_REQUIRED`).
  * Live threaded API endpoints (`/api/health`, `/api/commands`, `/api/sensors`, `/api/copy`, `/api/execute`).
  * Execution audit logging with microsecond timers and status tracking.

---

## 🚀 Quick Start

1. Double-click [`Launch_CommandScout.bat`](Launch_CommandScout.bat) (or launch from Desktop / Start Menu shortcut).
2. Browser opens automatically to **`http://127.0.0.1:8899`**.
3. Select your target environment (`Linux`, `Windows`, `Android`), pick a tool, tweak parameters, and hit **1-Click Copy** or **Execute** through the safety gate!
