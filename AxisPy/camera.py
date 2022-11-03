from requests.auth import HTTPDigestAuth
import requests
import logging


class AxisConfigure:

    def __init__(self, ip, username, password, debug=False, timeout=0.5):
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
        self.__timeout = timeout

    def __debug(self, message):
        if self.__debug:
            print("[DEBUG]:\t\t" + message)

    def __run_and_check_func(self, func):
        result = func()
        if result:
            self.__debug(func.__name__ + "\tWas Successful")
        else:
            self.__debug(func.__name__ + "\tWas NOT Successful")

    def __send_request(self, parameters, endpoint, get=False, auth=True, check_response=True):
        formatted_url = self.__url.format(self.ip, endpoint)
        response = None
        if auth:
            digest_auth = HTTPDigestAuth(self.__username, self.__password)
            if get:
                response = requests.get(formatted_url, auth=digest_auth, params=parameters, timeout=self.__timeout)
                if 'error' in response.json().keys():
                    self.__send_request(parameters, endpoint, get=not get, auth=auth, check_response=check_response)
            else:
                response = requests.post(formatted_url, auth=digest_auth, json=parameters, timeout=self.__timeout)
        else:
            if get:
                response = requests.get(formatted_url, params=parameters, timeout=self.__timeout)

        if check_response:
            return self.__response_is_ok(response)
        else:
            return response

    def __response_is_ok(self, response):
        if isinstance(response, requests.Response):
            if 'error' not in response.json().keys():
                return True
            else:
                return False

    def get_device_information(self):
        """Gets Axis camera devices information

        Returns
        -------
        requests.Response
            the response the camera gave from the API call
        """

        new_params = {'apiVersion': '1.2', 'method': 'getAllUnrestrictedProperties'}
        old_params = {'apiVersion': '1.0', 'method': 'getAllProperties'}
        result =  self.__send_request(new_params, self.__device_info, check_response=False)
        if self.__response_is_ok(result):
            return result
        else:
            return self.__send_request(old_params, self.__device_info, check_response=False)

    def get_serial_and_product(self):
        """Gets and parses the serial number and product number from Axis camera

        Returns
        -------
        tuple
            serial number and product number of Axis camera accordingly
        """

        response = self.get_device_information().json()
        # SerialNumber and ProductName
        SN = response['data']['propertyList']['SerialNumber']
        PN = response['data']['propertyList']['ProdShortName']
        return SN, PN

    def set_ip_and_dns_servers(self, new_ip, gateway, dnsserver_1, dnsserver_2=None):
        """Set static IP address and static DNS servers

        Parameters
        ----------
        new_ip: str
            New static IP address for Axis camera
        gateway: str
            Gateway for Axis camera
        dnsserver_1: str
            1st DNS server
        dnsserver_2: str, optional
            2nd DNS server

        Returns
        -------
        bool
            API call was successful
        """

        params = {'action': 'update', 'Network.BootProto': 'none', 'Network.Resolver.ObtainFromDHCP': 'no', 'Network.IPAddress': new_ip, 'Network.DefaultRouter': gateway, 'Network.DNSServer1': dnsserver_1, 'Network.DNSServer2': dnsserver_2}
        return self.__send_request(params, self.__general, get=True)

    def set_sd_card_ext4(self):
        """Set Inserted SD Card to EXT4 file type

        Returns
        -------
        bool
            API call was successful
        """

        params = {'schemaversion': 1, 'diskid': 'SD_DISK', 'filesystem': 'ext4'}
        return self.__send_request(params, self.__sd_card, get=True)

    def add_user(self, user, pwd, group='users', auth=True):
        """Add user to Axis camera

        Parameters
        ----------
        user: str
            username of the user
        pwd: str
            password of the user

        Returns
        -------
        bool
            API call was successful
        """

        params = {'action': 'add', 'user': user, 'pwd': pwd, 'grp': group, 'strict_pwd': 1, 'sgrp': 'viewer:operator:admin:ptz'}
        return self.__send_request(params, self.__users, get=True, auth=auth)

    def set_ntp_server(self, ntp_server):
        """Set NTP server

        Parameters
        ----------
        ntp_server: str
            NTP server for camera

        Returns
        -------
        bool
            API call was successful
        """

        params = {"apiVersion":"1.1","method":"setNTPClientConfiguration","params":{"enabled":True,"serversSource":"static","staticServers":[ntp_server]}}
        return self.__send_request(params, self.__ntp)

    def set_ntp_dhcp_mode(self, dhcp):
        """Set NTP DHCP mode

        'no' turns NTP DHCP off, while 'yes' turn NTP DHCP on

        Parameters
        ----------
        dhcp: str
            NTP DHCP mode. 'no'=off, 'yes'=on

        Returns
        -------
        bool
            API call was successful
        """

        params = {'action': 'update', 'Time.ObtainFromDHCP': dhcp}
        return self.__send_request(params, self.__general)

    def set_zoom_limit(self, limit):
        """Set the zoom limit for camera

        10909 seems to be the first digital option, and 9999 is the last mechanical option

        Parameters
        ----------
        limit: int
            Zoom limit for Axis camera

        Returns
        -------
        bool
            API call was successfull
        """

        params = {'action': 'update', 'PTZ.Limit.L1.MaxZoom': limit}
        return self.__send_request(params, self.__general, get=True)

    def set_wdr(self, state):
        """Set WDR option to on or off

        Parameters
        ----------
        state: str
            State to update WDR option to. 'on'=on, 'off'=off

        Returns
        -------
        bool
            API was successfull
        """

        params = {'action': 'update', 'ImageSource.I0.Sensor.WDR': state}
        return self.__send_request(params, self.__general, get=True)

    def set_ir_cut_filter(self, state):
        """Set IR cut filter to on or off

        Parameters
        ----------
        state: str
            State to update IR cut filter to. 'yes'=on, 'no'=off

        Returns
        -------
        bool
            API was successfull
        """

        params = {'action': 'update', 'ImageSource.I0.DayNight.IrCutFilter': state} # yes=on, no=off, auto=auto
        return self.__send_request(params, self.__general, get=True)

    def set_zipstream(self, strength=30):
        """Set Zipstream to low, medium, or high, higher, or extreme

        Parameters
        ----------
        strength: str
            Strength of Zipstream. 10=low, 20=medium, 30=high, 40=higher, 50=extreme

        Returns
        -------
        bool
            API call was successfull
        """

        params = {'strength': strength}
        return self.__send_request(params, self.__zipstream, get=True)

    def set_time_to_home(self, seconds):
        """Set time to home of ptz

        Parameters
        ----------
        seconds: int
            Seconds to wait until it returns back to home position

        Returns
        -------
        bool
            API call was successfull
        """

        params = {'action': 'update', 'PTZ.Various.V1.ReturnToOverview': seconds}
        return self.__send_request(params, self.__general, get=True)

    def create_dynamic_overlay(self, text):
        """Create a dynamic overlay on the video

        Parameters
        ----------
        text: str
            Text to display on the dynamic overlay. i.e. %D %T:%f

        Returns
        -------
        bool
            API call was successfull
        """

        params = {"apiVersion":"1.0","method":"addText","params":{"camera":1,"text":text}}
        response = self.__send_request(params, self.__dynam_overlay)
