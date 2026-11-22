import argparse
import time

import requests
from rich.console import Console
from rich.live import Live
from rich.text import Text

from ip_info import get_public_ipv4
from network_scan import get_local_ip, find_interface, scan_network, show_devices
from helpers import get_network_range

console = Console()


# Send the scan to the Cyber_Watch server, using the agent token
def send_scan(server, token, public_ip, devices):
    url = server.rstrip("/") + "/api/scans"
    body = {"public_ip": public_ip, "devices": devices}
    headers = {"X-Agent-Token": token}
    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)
    except requests.RequestException:
        console.print("[red]> server not reachable. Is it running?[/red]")
        return False

    if response.status_code == 200:
        console.print("[green]> scan sent to the server[/green]")
        return True

    console.print(
        "[red]> server refused the scan: " + str(response.status_code) + "[/red]"
    )
    console.print("[red]> " + response.text + "[/red]")
    return False


# One full scan: public IP, network scan, table, send to the server
def run_cycle(server, token, cycle):
    console.rule("[bold green]CYBER_WATCH - Agent (scan #" + str(cycle) + ")")
    console.print("[green]>[/green] time: " + time.strftime("%H:%M:%S"))

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
    send_scan(server, token, public_ip, devices)


# Countdown shown between two scans
def wait_with_countdown(seconds):
    with Live(refresh_per_second=4, transient=True) as live:
        for remaining in range(seconds, 0, -1):
            live.update(
                Text(
                    "> next scan in " + str(remaining) + " s   (Ctrl+C to stop)",
                    style="cyan",
                )
            )
            time.sleep(1)


def main():
    # Read the options given in the command line
    parser = argparse.ArgumentParser(description="Cyber_Watch agent")
    parser.add_argument("--token", help="your agent token (starts with cw_)")
    parser.add_argument(
        "--server", default="http://127.0.0.1:8000", help="server address"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="seconds between scans (0 = scan once, minimum 10)",
    )
    args = parser.parse_args()

    # If no token was given, ask for it
    token = args.token
    if not token:
        token = input("Agent token: ").strip()

    # Consent question: we scan only our own network
    answer = input(
        "Scan your own network and send the result to " + args.server + "? (y/n): "
    )
    if answer.lower() != "y":
        console.print("[red]> cancelled[/red]")
        return

    # Live mode needs at least 10 seconds (the free IP APIs have usage limits)
    interval = args.interval
    if interval != 0 and interval < 10:
        interval = 10

    cycle = 1
    try:
        while True:
            run_cycle(args.server, token, cycle)
            if interval == 0:
                break
            wait_with_countdown(interval)
            console.clear()
            cycle += 1
    except KeyboardInterrupt:
        console.print("\n[yellow]> agent stopped by the user[/yellow]")


if __name__ == "__main__":
    main()
