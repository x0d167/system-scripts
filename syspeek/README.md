✅ Systems & Statuses to Check
🧮 System Basics

    OS info (uname -a, /etc/os-release)

    Kernel version

    Uptime

    Hostname

    System load (1m, 5m, 15m)

💾 Disk & Memory

    Disk usage (df -h, maybe /home or /)

    RAM usage (free -h or psutil)

    Swap usage

🌐 Network

    Active interfaces and IP addresses (ip a)

    Default route (ip r)

    DNS status (systemd-resolve --status or resolvectl)

    VPN status (if applicable; e.g., protonvpn-cli status)

🔒 Security / Auth

    UFW status

    Fail2ban status

    Who is logged in (who, w)

    Last login (last -n 1)

🔧 Configuration Checks

    Dotfiles repo: git clean? (git status --porcelain)

    Syncthing running? (systemctl --user status syncthing)

    Services of interest (systemctl status foo)

☁️ Accounts & Connectivity

    GitHub connectivity (ssh -T git@github.com)

    Internet up? (e.g., ping or curl a known server)

    Check for updates (dnf check-update, etc.)
