import socket
import requests
from scapy.all import ARP, Ether, srp, conf
from rich import box
from rich.console import Console
from rich.table import Table

console = Console()


# Find our private IP (the address of this laptop on the local network)
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


# Find the network card that uses this IP
# (important when VirtualBox adds virtual network cards)
def find_interface(ip):
    for iface in conf.ifaces.values():
        if getattr(iface, "ip", None) == ip:
            return iface
    return conf.iface


# Try to get the name of a device from its IP
def get_hostname(ip):
    try:
        return socket.gethostbyname_ex(ip)[0] if False else socket.gethostbyaddr(ip)[0]
    except Exception:
        return "-"


# Ask a public API for the manufacturer of a MAC address
# (used only when the offline database does not know it)
def get_vendor_online(mac):
    try:
        response = requests.get(
            "https://api.macvendors.com/" + mac,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=4,
        )
        if response.status_code == 200:
            return response.text.strip()
    except requests.RequestException:
        pass
    return None


# Find the manufacturer of a device from its MAC address
# Phones often use a private (random) MAC, so no vendor can be found
def get_vendor(mac):
    first_byte = int(mac.split(":")[0], 16)
    # If this bit is 1, the MAC address is locally administered (random)
    if first_byte & 2:
        return "Random MAC"

    # First try: offline database inside Scapy
    try:
        vendor = conf.manufdb._get_manuf(mac)
        if vendor and vendor.lower() != mac.lower():
            return vendor
    except Exception:
        pass

    # Second try: online API
    vendor = get_vendor_online(mac)
    if vendor:
        return vendor
    return "Unknown"


# Send an ARP request to the whole network: "who has this IP?"
# Every device that answers gives us its IP and MAC address
def scan_network(network, iface):
    packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network)
    answered = srp(packet, iface=iface, timeout=3, verbose=False)[0]
    devices = []
    for sent, received in answered:
        device = {
            "ip": received.psrc,
            "mac": received.hwsrc,
            "vendor": get_vendor(received.hwsrc),
            "hostname": get_hostname(received.psrc),
        }
        devices.append(device)
    return devices


# Show the devices in a compact table (fits in 80 characters)
def show_devices(devices, my_ip):
    table = Table(box=box.ROUNDED, border_style="green", header_style="bold green")
    table.add_column("IP", no_wrap=True)
    table.add_column("MAC", no_wrap=True, style="cyan")
    table.add_column("VENDOR", max_width=16, overflow="ellipsis", no_wrap=True, style="yellow")
    table.add_column("HOST", max_width=12, overflow="ellipsis", no_wrap=True)

    for device in devices:
        if device["ip"] == my_ip:
            ip_text = "[bold green]" + device["ip"] + " *[/bold green]"
        else:
            ip_text = device["ip"]
        table.add_row(ip_text, device["mac"], device["vendor"], device["hostname"])

    console.print(table)
    console.print("[green]* = this laptop[/green]")


def main():
    console.rule("[bold green]CYBER_WATCH - Network scan")
    my_ip = get_local_ip()
    iface = find_interface(my_ip)
    network = my_ip.rsplit(".", 1)[0] + ".0/24"

    console.print("[green]>[/green] your IP     : " + my_ip)
    console.print("[green]>[/green] network card: " + str(iface.name))
    console.print("[green]>[/green] scan range  : " + network)

    # Consent question: we scan only our own network
    answer = input("Scan your own network? (y/n): ")
    if answer.lower() != "y":
        console.print("[red]> scan cancelled[/red]")
        return

    console.print("[green]>[/green] scanning...")
    devices = scan_network(network, iface)
    console.print("")
    show_devices(devices, my_ip)
    console.print("[bold green]>[/bold green] " + str(len(devices)) + " device(s) found")


if __name__ == "__main__":
    main()