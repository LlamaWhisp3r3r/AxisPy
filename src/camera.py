from requests.auth import HTTPDigestAuth
import requests


class AxisConfigure:

    def __init__(self, ip, username, password, debug=True):
        self.ip = ip
        self.__username = username
        self.__password = password
        self.__debug = debug

        # Axis API Endpoints
        self.__dynam_overlay = 'dynamicoverlay/dynamicoverlay.cgi'
        self.__general = 'param.cgi'
        self.__ptz = 'com/ptz.cgi'
        self.__time = 'time.cgi'
        self.__ntp = 'ntp.cgi'
        self.__users = 'pwdgrp.cgi'
        self.__device_info = 'basicdeviceinfo.cgi'
        self.__sd_card = 'disks/properties/setrequiredfs.cgi'
        self.__default_login = "pwdroot/pwdroot.cgi"
        self.__zipstream = 'zipstream/setstrength.cgi'
        self.__url = 'http://{}/axis-cgi/{}'

    def __debug(self, message):
        if self.__debug:
            print("[DEBUG]:\t\t" + message)

    def config(self):
        pass

    def __run_and_check_func(self, func):
        result = func()
        if result:
            self.__debug(func.__name__ + "\tWas Successful")
        else:
            self.__debug(func.__name__ + "\tWas NOT Successful")

    def __send_request(self, parameters, endpoint, auth=True, check_response=True):
        formatted_url = self.__url.format(self.ip, endpoint)
        response = None
        if auth:
            digest_auth = HTTPDigestAuth(self.__username, self.__password)
            response = requests.post(formatted_url, auth=digest_auth, json=parameters)
        else:
            response = requests.post(formatted_url, json=params)

        if check_response:
            return self.__response_is_ok(response)
        else:
            return response

    def __response_is_ok(self, response):
        if isinstance(response, requests.Response):
            if response.status_code == 200:
                return True
            else:
                return False

    def get_device_information(self):
        params = {'apiVersion': '1.0', 'context': 'Client defined request ID', 'method': 'getAllProperties'}
        return self.__send_request(params, self.__device_info, check_response=False)

    def get_serial_and_product(self):
        response = self.get_device_information()
        # SerialNumber and ProductName
        SN = response['data']['propertyList']['SerialNumber']
        PN = response['data']['propertyList']['ProdShortName']
        return SN, PN

    def set_ip_and_dns_servers(self, new_ip='192.168.1.3', gateway='192.168.1.1', dnsserver_1='8.8.8.8', dnsserver_2='192.168.1.1'):
        params = {'action': 'update', 'Network.BootProto': 'none', 'Network.Resolver.ObtainFromDHCP': 'no', 'Network.IPAddress': new_ip, 'Network.DefaultRouter': gateway, 'Network.DNSServer1': dnsserver_1, 'Network.DNSServer2': dnsserver_2}
        return self.__send_request(params, self.__general)

    def set_sd_card_ext4(self):
        # --- Flip storage switch ---
        params = {'schemaversion': 1, 'diskid': 'SD_DISK', 'filesystem': 'ext4'}
        return self.__send_request(params, self.__sd_card)

    def add_user(self, user='valorence', pwd="Covert1234"):
        params = {'action': 'add', 'user': user, 'pwd': pwd, 'grp': 'users', 'strict_pwd': 1, 'sgrp': 'viewer:operator:admin:ptz'}
        return self.__send_request(params, self.__users)

    def set_ntp_server(self, ntp_server='ntp.axis.com'):
        params = {"apiVersion":"1.1","method":"setNTPClientConfiguration","params":{"enabled":True,"serversSource":"static","staticServers":[ntp_server]}}
        return self.__send_request(params, self.__ntp)

    def set_ntp_dhcp_mode(self, dhcp='no'):
        params = {'action': 'update', 'Time.ObtainFromDHCP': dhcp}
        return self.__send_request(params, self.__general)

    def set_zoom_limit(self, limit='10909'):
        params = {'action': 'update', 'PTZ.Limit.L1.MaxZoom': limit} # 10909 seems to be the first digital option, and 9999 is the last mechanical option
        return self.__send_request(params, self.__general)

    def update_wdr(self, state='on'):
        params = {'action': 'update', 'ImageSource.I0.Sensor.WDR': state}
        return self.__send_request(params, self.__general)

    def set_ir_cut_filter(self, state='yes'):
        params = {'action': 'update', 'ImageSource.I0.DayNight.IrCutFilter': state} # yes=on, no=off, auto=auto
        response = self.__send_request(params, self.__general)
        return response.text

    def update_zipstream(self, strength=30):
        params = {'strength': strength} # 10=low, 20=medium, 30=high, 40=higher, 50=extreme
        return self.__send_request(params, self.__zipstream)

    def set_time_to_home(self, seconds=1500):
        params = {'action': 'update', 'PTZ.Various.V1.ReturnToOverview': seconds} # seconds is the amount of seconds it takes to go back to home position
        return self.__send_request(params, self.__general)

    def create_dynamic_overlay(self, text="%D %T:%f"):
        params = {"apiVersion":"1.0","method":"addText","params":{"camera":1,"text":text}}
        response = self.__send_request(params, self.__dynam_overlay)

    def factory_login(self, user='root', pwd='Avscle2010'):
        # Should be able to do this with requests instead of selenium
        # Need to manually go down and plug into the router

        params = {'action': 'update', 'user': user, 'pwd': pwd}
        url = self.__url.format(self.ip, self.__default_login)
        response = requests.post(url, json=params)
        print(response.text)
