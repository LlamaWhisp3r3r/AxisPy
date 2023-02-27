from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import time

def get_only_axis_devices():

    overall_devices = run_scan()
    # This function only sees bonjour clients that have AXIS in their name
    axis_devices = dict()
    for name, ip_addresses in overall_devices.items():
        if 'axis' in name.lower():
            axis_devices[name] = get_local_ip_from_list(ip_addresses)
    return axis_devices


def run_scan():
    zeroconf = Zeroconf()
    listener = MyListener()
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
    try:
        time.sleep(10)
    finally:
        zeroconf.close()
    return listener.overall_devices

def get_local_ip_from_list(ip_list):

    for ip in ip_list:
        # Check for apipa address
        if '169.254' not in ip and ipv6_character_in_ip_address(ip):
            return ip
    return None

def ipv6_character_in_ip_address(ip_address):
    # List of ipv6 characters
    ipv6_list = ['a', 'b', 'c', 'd', 'e', 'f']

    for ipv6 in ipv6_list:
        if ipv6 in ip_address:
            return False
    return True

def display_devices_on_network(device_list):

    count = 0
    for name, ip_address in device_list.items():
        count += 1
        print(f"[{count}] {name}: {ip_address}")

def get_selected_device(device_list, selected_device):
    count = 0
    for name, ip_address in device_list.items():
        count += 1
        if count == selected_device:
            return f"[{count}] {name}: {ip_address}"


class MyListener(ServiceListener):

    def __init__(self):
        self.overall_devices = dict()

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} updated")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        name = name.split("._http")[0]
        self.overall_devices[name] = info.parsed_addresses()


if __name__ == '__main__':
    axis_devices = get_only_axis_devices()
    display_devices_on_network(axis_devices)
    camera_select = int(input("Please select the camera desired>>> "))
    get_selected_device(axis_devices, camera_select)



