import requests
from rich.console import Console
from rich.table import Table

console = Console()


# Ask a public API for our public IPv4 address
def get_public_ipv4():
    try:
        return requests.get("https://api.ipify.org", timeout=5).text
    except requests.RequestException:
        return None


# Ask a public API for our public IPv6 address
# (it fails if the network has no IPv6, this is normal)
def get_public_ipv6():
    try:
        return requests.get("https://api6.ipify.org", timeout=5).text
    except requests.RequestException:
        return None


# Ask public APIs for details about an IP: country, city, ISP, ASN...
# First choice: ipapi.co. If it fails, second choice: ipwho.is
def get_ip_details(ip):
    # --- First choice: ipapi.co ---
    try:
        response = requests.get(
            "https://ipapi.co/" + ip + "/json/",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        data = response.json()
        if "error" not in data:
            return {
                "country": data.get("country_name"),
                "country_code": data.get("country_code"),
                "city": data.get("city"),
                "region": data.get("region"),
                "isp": data.get("org"),
                "asn": data.get("asn"),
                "timezone": data.get("timezone"),
                "lat": data.get("latitude"),
                "lon": data.get("longitude"),
                "source": "ipapi.co",
            }
        console.print("[yellow]ipapi.co said: " + str(data.get("reason")) + "[/yellow]")
    except (requests.RequestException, ValueError):
        console.print("[yellow]ipapi.co not reachable[/yellow]")

    # --- Second choice: ipwho.is ---
    try:
        data = requests.get("https://ipwho.is/" + ip, timeout=5).json()
        if data.get("success"):
            connection = data.get("connection", {})
            timezone = data.get("timezone", {})
            return {
                "country": data.get("country"),
                "country_code": data.get("country_code"),
                "city": data.get("city"),
                "region": data.get("region"),
                "isp": connection.get("isp"),
                "asn": connection.get("asn"),
                "timezone": timezone.get("id"),
                "lat": data.get("latitude"),
                "lon": data.get("longitude"),
                "source": "ipwho.is",
            }
    except (requests.RequestException, ValueError):
        pass

    return None


# Build and print the formatted table
def show_public_identity():
    ipv4 = get_public_ipv4()
    ipv6 = get_public_ipv6()

    table = Table(title="CYBER_WATCH - Public IP identity", border_style="green")
    table.add_column("FIELD", style="bold green")
    table.add_column("VALUE", style="cyan")

    table.add_row("Public IPv4", ipv4 or "not available")
    table.add_row("Public IPv6", ipv6 or "not available (no IPv6 on this network)")

    if ipv4:
        details = get_ip_details(ipv4)
        if details:
            table.add_row("Country", str(details["country"]) + " (" + str(details["country_code"]) + ")")
            table.add_row("City / Region", str(details["city"]) + " / " + str(details["region"]))
            table.add_row("ISP", str(details["isp"]))
            table.add_row("ASN", str(details["asn"]))
            table.add_row("Timezone", str(details["timezone"]))
            table.add_row("Coordinates", str(details["lat"]) + ", " + str(details["lon"]))
            table.add_row("Data source", str(details["source"]))
        else:
            table.add_row("Details", "all APIs unavailable")

    console.print(table)


# Run the program (this line must stay at the very left, with no spaces)
if __name__ == "__main__":
    show_public_identity()
    