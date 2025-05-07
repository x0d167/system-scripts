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
    print(disk)
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

    print(mem)
    return mem


################################################################
#                          NETWORK                             #
################################################################

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


if __name__ == "__main__":
    main()
