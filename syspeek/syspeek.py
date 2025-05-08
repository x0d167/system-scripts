import subprocess
from rich.console import Console
from rich.table import Table


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


################################################################
#                          SECURITY                            #
################################################################


################################################################
#                       CONFIG CHECKS                          #
################################################################


################################################################
#                  ACCOUNTS & CONNECTIVITY                     #
################################################################


################################################################
#                   RENDER SYSTEM SUMMARY                      #
################################################################


def render_system_summary(summary: dict):
    """Use rich to present the system summary"""
    table = Table(title="System Overview")

    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    for key, value in summary.items():
        row_style = None

        if "Load Avg" in key:
            try:
                percent_str = value.split("(")[1].split("%")[0]
                load_percent = float(percent_str)
                if load_percent >= 80:
                    row_style = "red"
            except (IndexError, ValueError):
                pass

        table.add_row(key, value, style=row_style)

    console = Console()
    console.print(table)


################################################################
#                      MAIN FUNCTION                           #
################################################################


def main():
    system_summary = get_system_summary()

    render_system_summary(system_summary)
    get_disk_usage()
    get_mem_usage()
    get_active_ip_interfaces()
    confirm_default_route()
    get_dns_status()


if __name__ == "__main__":
    main()
