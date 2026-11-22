
import argparse

import requests
from rich.console import Console

from ip_info import get_public_ipv4
from network_scan import get_local_ip, find_interface, scan_network, show_devices
from helpers import get_network_range

console = Console()

# Default server: users do not need to type --server
DEFAULT_SERVER = "https://cyber-watch-iq8p.onrender.com"


# Send the scan to the Cyber_Watch server, using the agent token
def send_scan(server, token, public_ip, devices):
    url = server.rstrip("/") + "/api/scans"
    body = {"public_ip": public_ip, "devices": devices}
    headers = {"X-Agent-Token": token}

    try:
        response = requests.post(
            url,
            json=body,
            headers=headers,
            timeout=60
        )
    except requests.RequestException:
        console.print("[red]> server not reachable. Is it running?[/red]")
        return False

    if response.status_code == 200:
        console.print("[green]> scan sent to the server[/green]")
        return True

    console.print("[red]> server refused the scan: " + str(response.status_code) + "[/red]")
    console.print("[red]> " + response.text + "[/red]")
    return False


def main():
    # Read the options given in the command line (--token and --server)
    parser = argparse.ArgumentParser(description="Cyber_Watch agent")

    parser.add_argument("--token", help="your agent token (starts with cw_)")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="server address")

    args = parser.parse_args()

    console.rule("[bold green]CYBER_WATCH - Agent")

    # If no token was given, ask for it
    token = args.token
    if not token:
        token = input("Agent token: ").strip()

    # Consent question: we scan only our own network
    answer = input("Scan your own network and send the result to " + args.server + "? (y/n): ")

    if answer.lower() != "y":
        console.print("[red]> cancelled[/red]")
        return

    # Step 1: public IP
    console.print("[green]>[/green] reading public IP...")
    public_ip = get_public_ipv4()
    console.print("[green]>[/green] public IP: " + str(public_ip))

    # Step 2: local network scan
    my_ip = get_local_ip()
    iface = find_interface(my_ip)
    network = get_network_range(my_ip)

    console.print("[green]>[/green] scanning " + network + " ...")

    devices = scan_network(network, iface)

    console.print("")
    show_devices(devices, my_ip)

    # Step 3: send to the server
    console.print("[green]>[/green] sending to the server...")

    success = send_scan(args.server, token, public_ip, devices)

    if success:
        console.print("[bold green]> CYBER_WATCH scan completed successfully![/bold green]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]> Agent stopped by user.[/yellow]")
    except Exception as error:
        console.print(f"\n[red]> Agent error: {error}[/red]")

    # Keep the window open when the .exe is started by double-click
    input("\nPress Enter to close...")
