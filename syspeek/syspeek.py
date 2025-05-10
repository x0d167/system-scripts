import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box


################################################################
#                      SYSTEM INFO                             #
################################################################


def get_os_info():
    """Process for capturing the current OS details"""
    # OS info has a lot of lines and we'll capture as dict
    os_info = {}
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if "=" in line:
                    # key/value split on '='
                    key, value = line.strip().split("=", 1)
                    # strip the "" from the value
                    os_info[key] = value.strip('"')
        return f"{os_info.get('PRETTY_NAME', 'Unknown OS')} ({os_info.get('ID', '')})"
    except FileNotFoundError:
        return "Unknown OS"


def get_kernel_version():
    result = subprocess.run(["uname", "-r"], capture_output=True, text=True)
    key, value = result.stdout.split("-", 1)
    return key.strip()


def get_uptime():
    """Get the uptime of the current machine"""
    result = subprocess.run(["uptime", "-p"], capture_output=True, text=True)
    return result.stdout.strip()


def get_hostname():
    """Simply pull the hostname"""
    result = subprocess.run(["hostname"], capture_output=True, text=True)
    return result.stdout.strip()


def get_load_averages():
    result = subprocess.run(["uptime"], capture_output=True, text=True)
    if result.returncode == 0:
        parts = result.stdout.strip().split("load average: ")
        if len(parts) > 1:
            load_str = parts[1].strip()
            one_min = float(load_str.split(",")[0].strip())
            cores = get_cpu_cores()
            load_percent = (one_min / cores) * 100
            return f"{load_str} ({load_percent:.1f}% of {cores} cores)"
    return "Unknown"


def get_cpu_cores():
    """Get the cpu core count using nproc"""
    result = subprocess.run(["nproc"], capture_output=True, text=True)
    cores = int(result.stdout.strip())
    return cores


def get_system_summary():
    """Get the system summary"""
    return {
        "OS": get_os_info(),
        "Kernel": get_kernel_version(),
        "Uptime": get_uptime(),
        "hostname": get_hostname(),
        "Load Avg (1m, 5m, 15m)": get_load_averages(),
    }


################################################################
#                      DISK & MEMORY                           #
################################################################


def get_disk_usage():
    """Get the relevant disk usage from df -h"""
    result = subprocess.run(["df", "-h"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    disk = {}

    for line in lines:
        if "/home" in line:
            if "pCloud" in line:
                drive = "pCloud"
            else:
                drive = "Home Disk"
            stats = line.split(maxsplit=5)
            total_size = stats[1]
            used = stats[2]
            free = stats[3]
            disk[drive] = f"{used} | {free} (of {total_size})"
    return disk


def get_mem_usage():
    """Get the system memory and swap usage with free -h"""
    result = subprocess.run(["free", "-h"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    mem = {}

    for line in lines:
        if ":" in line:
            stats = line.split()
            mem_type = stats[0].strip().split(":")[0]
            total = stats[1]
            used = stats[2]
            free = stats[3]

            mem[mem_type] = f"{used} | {free} (of {total})"

    return mem

def get_disk_mem_summary():
    """summarize the disk and memory details"""
    return {
            "Disk": get_disk_usage(),
            "Memory": get_mem_usage(),
    }
################################################################
#                          NETWORK                             #
################################################################


def get_active_ip_interfaces():
    """Get active interfaces with ip -brief a"""
    result = subprocess.run(["ip", "-brief", "a"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    ip_intfc = {}

    for line in lines:
        entry = line.split()
        if len(entry) >= 3:
            interface = entry[0]
            status = entry[1]
            if interface == "lo":
                continue
            for field in entry[2:]:
                if ":" not in field:  # likely an IPv4
                    ipv4 = field
                    ip_intfc[interface] = {"ip": ipv4, "status": status}
                    break

    return ip_intfc


def confirm_default_route():
    """Check ip r to confirm internet access is active"""
    result = subprocess.run(["ip", "r"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    default_route = {}

    for line in lines:
        entry = line.split()
        if entry and entry[0] == "default":
            device = entry[4]
            gateway = entry[2]
            default_route[device] = {"gateway": gateway}

    # print(default_route)
    return {"default routes": default_route}


def get_dns_status():
    """Retrieve DNS status with resolvectl"""
    result = subprocess.run(["resolvectl", "status"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    sections = {}
    current_section = None
    dns_status = {}

    for line in lines:
        if line == "Global":
            current_section = "Global"
            sections[current_section] = []
        elif line.startswith("Link"):
            interface = line.split("(")[1].split(")")[0]
            current_section = interface
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line.strip())

    for key, details in sections.items():
        if "Default Route: yes" in details:
            interface = key
            current_server = None
            dns_servers = []

            for line in details:
                if line.startswith("Current DNS Server:"):
                    current_server = line.split(":", 1)[1].strip()
                elif line.startswith("DNS Servers:"):
                    dns_servers = line.split(":", 1)[1].strip().split()

            dns_status = {
                "dns": {
                    "status": True,
                    "current_server": current_server,
                    "all_servers": dns_servers,
                    "interface": interface,
                }
            }
            break

    if not dns_status:
        dns_status = {
            "dns": {"status": False, "reason": "No active DNS interface found"}
        }

    return dns_status

def detect_vpn_status():
    """Basic VPN check using presence of VPN-like interfaces"""
    interfaces = get_active_ip_interfaces()
    for iface in interfaces:
        if any(keyword in iface.lower() for keyword in ["proton", "vpn", "tun", "wg"]):
            return {
                "vpn": {
                    "status": True,
                    "interface": iface,
                    "ip": interfaces[iface]["ip"]
                }
            }

    return {
        "vpn": {
            "status": False,
            "reason": "No active VPN interface detected"
        }
    }

def get_network_summary():
    """Gather all network-related information into a structured summary."""
    interfaces = get_active_ip_interfaces()
    default_routes = confirm_default_route()
    dns = get_dns_status()
    vpn = detect_vpn_status()

    summary = {
        "interfaces": interfaces,
        "default_routes": default_routes.get("default routes", {}),
        "dns": dns.get("dns", {}),
        "vpn": vpn.get("vpn", {}),
    }

    return summary

################################################################
#                          SECURITY                            #
################################################################

def check_firewall_status():
    """Check Firewalld status."""
    result = subprocess.run(["systemctl", "status", "firewalld"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    firewalld_status = {}

    for line in lines:
        if line.strip().startswith("Loaded"):
            if "firewalld.service; enabled;" in line:
                systemctl_status = {"Firewall enabled": "True"}
                firewalld_status["Firewalld"] = systemctl_status
            else:
                systemctl_status = {"Firewall enabled": "False"}
                firewalld_status["Firewalld"] = systemctl_status
        if line.strip().startswith("Active"):
            if "active (running)" in line:
                firewall_active_stat = {"Firewall running": "True"}
                firewalld_status["Firewalld"].update(firewall_active_stat)
            else:
                firewall_active_stat = {"Firewall running": "False"}
                firewalld_status["Firewalld"].update(firewall_active_stat)

    return firewalld_status


################################################################
#                   RENDER SYSTEM SUMMARY                      #
################################################################
def render_dashboard(system, network, firewall, disk_mem):
    console = Console()
    layout = Layout()

    # Top-level layout split into header + body
    layout.split(Layout(name="header", size=3), Layout(name="body", ratio=1))

    # Body is split into 2 rows: top(sys+net), bottom (security+storage)
    layout["body"].split(Layout(name="top", ratio=1), Layout(name="bottom", ratio=1))

    # Split top row horizontally into system + network
    layout["top"].split_row(Layout(name="system"), Layout(name="network"))

    # Split bottom row into security + resources (or future)
    layout["bottom"].split_row(Layout(name="security"), Layout(name="placeholder"))

    # HEADER
    layout["header"].update(Text("🖥️  syspeek: System Status Overview", style="bold cyan"))

    # SYSTEM PANEL
    layout["system"].update(render_system_panel(system, disk_mem))

    # NETWORK PANEL
    layout["network"].update(render_network_panel(network))

    # SECURITY PANEL
    layout["security"].update(render_security_panel(firewall))

    # Placeholder for future use
    layout["placeholder"].update(Panel(Text("Coming soon...", justify="center"), title="💾 Resources"))

    console.print(layout)

def render_network_panel(network):
    table = Table.grid(padding=(0, 1))
    interfaces = network.get("interfaces", {})
    for name, data in interfaces.items():
        ip = data.get("ip", "—")
        status = data.get("status", "—")
        symbol = "🟢" if "UP" in status.upper() or name == "proton0" else "🔴"
        table.add_row(f"{symbol} [bold]{name}[/]", f"{ip} ({status})")

    routes = network.get("default_routes", {})
    for iface, info in routes.items():
        table.add_row(f"🌐 Route ({iface})", f"Gateway: {info.get('gateway', '—')}")

    dns = network.get("dns", {})
    if dns.get("status"):
        current = dns.get("current_server", "—")
        all_servers = ", ".join(dns.get("all_servers", []))
        table.add_row("🧭 DNS", f"{current} (via {dns.get('interface', '—')})")
        if len(dns.get("all_servers", [])) > 1:
            table.add_row("", f"Alt: {all_servers}")
    else:
        table.add_row("🧭 DNS", "[red]❌ No DNS detected[/]")

    vpn = network.get("vpn", {})
    if vpn.get("status"):
        table.add_row("🔐 VPN", f"[green]Active[/] via {vpn.get('interface')} ({vpn.get('ip')})")
    else:
        table.add_row("🔐 VPN", "[yellow]Not detected[/]")

    return Panel(table, title="🌐 Network", box=box.ROUNDED)

def render_system_panel(system, disk_mem):
    table = Table.grid(padding=(0, 2))
    
    # 🧠 Basic System Info
    table.add_row("💻 [bold]OS[/]", system.get("OS", "—"))
    table.add_row("🧬 [bold]Kernel[/]", system.get("Kernel", "—"))
    table.add_row("🕒 [bold]Uptime[/]", system.get("Uptime", "—"))
    table.add_row("📛 [bold]Hostname[/]", system.get("hostname", "—"))

    # 🧮 Load Average
    load = system.get("Load Avg (1m, 5m, 15m)", "—")
    try:
        percent = float(load.split("(")[1].split("%")[0])
        style = "green" if percent < 50 else "yellow" if percent < 80 else "red"
        load_display = f"[{style}]{load}[/{style}]"
    except Exception:
        load_display = load
    table.add_row("📊 [bold]Load Avg[/]", load_display)

    # 💾 Disk Usage
    table.add_row("", "")  # spacer row
    disk = disk_mem.get("Disk", {})
    for label, usage in disk.items():
        table.add_row(f"💽 [bold]{label}[/]", usage)

    # 🧠 Memory Usage
    mem = disk_mem.get("Memory", {})
    for label, usage in mem.items():
        emoji = "🧠" if label == "Mem" else "🔃"
        table.add_row(f"{emoji} [bold]{label}[/]", usage)

    return Panel(table, title="🧠 System", box=box.ROUNDED)


def render_security_panel(firewall):
    from rich.align import Align
    from rich.panel import Panel
    from rich.text import Text

    status = firewall.get("Firewalld", {})
    enabled = status.get("Firewall enabled", "False") == "True"
    running = status.get("Firewall running", "False") == "True"

    if enabled and running:
        message = Text("✅ Firewall is ENABLED and ACTIVE", style="bold white on green", justify="center")
    elif not enabled and not running:
        message = Text("❌ Firewall is DISABLED and INACTIVE", style="bold white on red", justify="center")
    elif not enabled:
        message = Text("⚠️ Firewall is INACTIVE (not enabled)", style="bold black on yellow", justify="center")
    else:
        message = Text("⚠️ Firewall is ENABLED but NOT RUNNING", style="bold black on yellow", justify="center")

    return Panel(Align.center(message, vertical="middle"), title="🔐 Security", height=5, padding=1)
################################################################
#                      MAIN FUNCTION                           #
################################################################


def main():
    system_summary = get_system_summary()
    network_summary = get_network_summary()
    firewall_summary = check_firewall_status()
    disk_mem_summary = get_disk_mem_summary()

    render_dashboard(system_summary, network_summary, firewall_summary, disk_mem_summary)


if __name__ == "__main__":
    main()
