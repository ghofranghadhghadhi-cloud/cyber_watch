# Small functions that need no network, so they are easy to test


# Check if a MAC address is random (private).
# Phones use this for privacy. If the second bit of the first byte is 1,
# the MAC is "locally administered" (random).
def is_random_mac(mac):
    first_byte = int(mac.split(":")[0], 16)
    return (first_byte & 2) != 0


# Build the network range to scan from our IP address
# Example: 192.168.74.21 -> 192.168.74.0/24
def get_network_range(ip):
    return ip.rsplit(".", 1)[0] + ".0/24"