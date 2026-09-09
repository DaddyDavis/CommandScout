# CommandScout: Tactical Syntax & Command Scaffolding Studio

**Assistive Universal Design & Cognitive Scaffolding for Cyber Operations**  
*Engineered by Austin Davis (U.S. Army Veteran 19D / DeVry University Cyber Security Student)*

---

## Overview

**CommandScout** is a high-speed, offline-first command scaffolding studio and syntax builder. It was purpose-built to solve two critical operational challenges:
1. **Physical Ergonomics & Assistive Technology**: Designed specifically for operators with severe motor/hand injuries to eliminate tedious, error-prone manual typing of complex security command syntax, escaping flags, and delimiters.
2. **Cognitive Scaffolding for ADHD**: Mitigates working memory exhaustion and syntax frustration by transforming command line parameters (IPs, Ports, BSSIDs, Interfaces, Wordlists) into intuitive, visual input badges with live dynamic syntax previews.

---

## Key Architectural Features

### 1. Dual-Ecosystem Command Hub
* **Instant 1-Click Environment Switching**: Toggle between **`[Linux & Kali Security]`** and **`[Windows & PowerShell]`** in real-time.
* Seamlessly swaps category filters, command catalogs, terminal prompt prefixes (`user@kali:~$` vs `PS C:\Users\Austin>`), and underlying execution targets.

### 2. Comprehensive 28-Tool / 93-Recipe Arsenal (`commands_db.json`)
* **Linux & Kali Security (14 Engines / 49 Recipes)**:
  * **Network Recon & Scanning**: Nmap (Stealth SYN, Aggressive OS/Version, NSE Vuln, Subnet Discovery, UDP Top Ports, SMB Share & Security Mode).
  * **Wireless & RF Auditing**: Kismet (monitor mode, headless fixed-channel logging), Aircrack-ng (airmon-ng, airodump-ng handshake capture, aireplay-ng deauth, aircrack-ng dictionary crack), PMKID Clientless WPA2 Attack (`hcxdumptool` and `hcxpcapngtool` to Hashcat mode 22000), Wireless Deauth & Survey (`aireplay-ng` burst, `airodump-ng` spectrum survey).
  * **Packet Inspection & Forensics**: Tshark (HTTP sniffer, DNS query monitor, cleartext credentials), Linux Incident Response (`journalctl` live SSH brute-force monitor, active user sessions, non-standard SUID binaries, `lsof` socket mapping).
  * **Privilege Escalation**: Linux Privilege Escalation Hunter (`sudo -l` audit, writable `/etc` and `/var` search, crontab/systemd timer inspection, kernel release identification).
  * **Web, Exploitation & Pivots**: Hydra (SSH/FTP parallel brute force), Gobuster (directory & subdomain fuzzing), Hashcat (NTLM & WPA2), Metasploit/Msfvenom (reverse x64 shells & listeners), Netcat & Socat (port redirection relays), Chisel (reverse SOCKS5 pivot tunnels).
* **Windows & PowerShell (14 Engines / 44 Recipes)**:
  * **DFIR & Event Auditing**: Event Log Hunter (Security Event IDs 4625 failed logins, 4624 interactive sessions, 4688 process lineage, Defender exclusion audits), Persistence & Autostart Hunter (Run/RunOnce registry keys, non-Microsoft scheduled tasks, startup LNK shortcuts, WMI `__EventConsumer` persistence), Rapid IR Live Triage (parent-child process lineage with full command lines, `USBSTOR` connection history, Alternate Data Streams `Zone.Identifier` MOTW audits).
  * **Active Directory & Domain Recon**: Zero-footprint ADSI .NET LDAP queries (PDC role owner, Domain Admins enumeration, password age and expiration audits, server OS discovery).
  * **Host Hardening & Defense**: Windows Defender Engine & Signature telemetry, LSASS `RunAsPPL` memory protection audit, Firewall profiles audit, Controlled Folder Access (ransomware shield).
  * **Network & Diagnostics**: `Get-NetTCPConnection` correlated to process names, `Test-NetConnection` port probes, DNS cache flush, `Get-NetIPConfiguration` full adapter dump, continuous millisecond latency/jitter monitor.
  * **System Administration**: Winget package manager (search, unattended installs, export), Sysinternals (Autoruns CSV CLI audit, ProcMon boot logging, unquoted service paths), Hardware S.M.A.R.T. disk health, `powercfg /batteryreport` HTML telemetry, driverquery audit, DISM/SFC component store repair, WSL2 & `usbipd` passthrough, and Certutil hashing/encoding.

### 3. Resilient Multi-Tier Clipboard Injection
* **1-Click Copy**: Injects scaffolded commands directly into the OS clipboard using the browser API with a zero-permission `document.execCommand('copy')` hidden-textarea fallback.
* **Auto-Select Command Bar**: Clicking anywhere inside the bottom sticky command bar automatically selects the entire syntax string for instant manual copying.
* **Audio Feedback**: Plays an acoustic confirmation chime (Web Audio API / `winsound.MessageBeep`) when copied.

### 4. High-Contrast OLED Visual Ergonomics
* Tuned deep-black design system (`#030508`) paired with high-voltage neon green (`#00ff66`), laser crimson (`#ff2244`), and electric cyan accents optimized for 144Hz IPS display panel calibration and low eye fatigue.

---

## Empirical Field Validation

* **VirtualBox USB Passthrough**: Successfully routed a Qualcomm Atheros AR9271 USB Wi-Fi adapter into a Kali Linux VM. Diagnosed and resolved a Windows kernel BSOD (`Bugcheck 0x139 KERNEL_SECURITY_CHECK_FAILURE / LIST_ENTRY_CORRUPTED`) triggered by VirtualBox's NDIS filter driver (`VBoxNetLwf.sys`).
* **Layer 2 802.11 Injection**: Scaffolded and executed live 802.11 deauth bursts using `aireplay-ng` locked to Channel 1, achieving 100% two-way Layer 2 frame receipt (`[64|64 ACKs]`) against IoT hardware (Roku, Inc. `84:EA:ED:BF:C6:05`).
* **WPA2 4-Way Handshake Interception**: Coordinated multi-terminal sniffing via `airodump-ng` and deauth stimulation to capture a complete 4-Way WPA2 EAPOL Handshake (`davis_capture-01.cap`), verified via `aircrack-ng`.

---

## Quick Start

1. Double-click [`Launch_CommandScout.bat`](Launch_CommandScout.bat)
2. Open your browser to: **`http://localhost:8899`**
3. Select your environment & category, adjust parameters, and click **1-Click Copy**!
