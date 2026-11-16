from helpers import is_random_mac, get_network_range


# A phone MAC with a random address (0x72 has the "local" bit set)
def test_random_mac_is_detected():
    assert is_random_mac("72:f2:ab:df:cb:5a") is True


# A real hardware MAC (0x24 does not have the "local" bit)
def test_real_mac_is_not_random():
    assert is_random_mac("24:b2:b9:60:93:93") is False


# The network range is built from the IP of the laptop
def test_network_range():
    assert get_network_range("192.168.74.21") == "192.168.74.0/24"