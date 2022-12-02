from requests.auth import HTTPDigestAuth
from requests import request
try:
    from AxisPy.check_axis_response import check_response
except ModuleNotFoundError:
    from check_axis_response import check_response
import requests
import xml.etree.ElementTree as ET
from json.decoder import JSONDecodeError
from xml.etree.ElementTree import ParseError
import logging

class AxisConfigure:

    def __init__(self, ip, username='root', password='pass', debug=False, timeout=0.5):
        self.ip = ip
        self.__username = username
        self.__password = password
        self.__default_password = "pass"
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
        self.__list_sd = 'disks/list.cgi'
        self.__default_login = "pwdroot/pwdroot.cgi"
        self.__zipstream = 'zipstream/setstrength.cgi'
        self.__light_control = 'lightcontrol.cgi'
        self.__capture_mode = 'capturemode.cgi'
        self.__system_ready = 'systemready.cgi'
        self.__restart_cgi = 'restart.cgi'
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
    
    def __try_catch(func):
        def inner(self, *args, **kwargs):
            try:
                print(func.__name__)
                return func(self, *args, **kwargs)
            except JSONDecodeError:
                return None
            except ParseError:
                return []
            except IndexError:
                return []
        return inner

    def __send_request(self, method, endpoint, auth=True, check=True, **kwargs):
        formatted_url = self.__url.format(self.ip, endpoint)
        proxies = {'http': 'http://127.0.0.1:8080',
                   'https': 'http://127.0.0.1:8080'}
        response = None
        digest_auth = None
        
        if auth:
            digest_auth = HTTPDigestAuth(self.__username, self.__password)
    
        response = request(method, formatted_url, auth=digest_auth, timeout=self.__timeout, proxies=proxies, **kwargs)

        if check:
            return check_response(response)
        else:
            return response

    def get_device_information(self, auth=True):
        """Gets Axis camera devices information

        Returns
        -------
        requests.Response
            the response the camera gave from the API call
        """

        params = {'apiVersion': '1.2',
                      'method': 'getAllUnrestrictedProperties'}
        return self.__send_request(
            "POST", self.__device_info, check=False, auth=auth, json=params)

    @__try_catch
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

        params = {'action': 'update', 'Network.BootProto': 'none', 'Network.Resolver.ObtainFromDHCP': 'no', 'Network.IPAddress': new_ip,
                  'Network.DefaultRouter': gateway, 'Network.DNSServer1': dnsserver_1, 'Network.DNSServer2': dnsserver_2}
        return self.__send_request("GET", self.__general, params=params)

    def set_sd_card_ext4(self):
        """Set Inserted SD Card to EXT4 file type

        Returns
        -------
        bool
            API call was successful
        """

        params = {'schemaversion': 1,
                  'diskid': 'SD_DISK', 'filesystem': 'ext4'}
        return self.__send_request("GET", self.__sd_card, params=params)

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

        params = {'action': 'add', 'user': user, 'pwd': pwd, 'grp': group,
                  'strict_pwd': 1, 'sgrp': 'viewer:operator:admin:ptz'}
        return self.__send_request("GET", self.__users, params=params, auth=auth)

    def set_ntp_server(self, ntp_server1, ntp_server2=None):
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

        params = {"apiVersion": "1.1", "method": "setNTPClientConfiguration", "params": {
            "enabled": True, "serversSource": "static", "staticServers": [ntp_server1, ntp_server2]}}
        return self.__send_request("POST", self.__ntp, json=params)

    def set_ntp_dhcp_mode(self, dhcp):
        """Set NTP DHCP mode

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
        return self.__send_request("GET", self.__general, params=params)

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
        return self.__send_request("GET", self.__general, params=params)

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
        return self.__send_request("GET", self.__general, params=params)

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

        # yes=on, no=off, auto=auto
        params = {'action': 'update',
                  'ImageSource.I0.DayNight.IrCutFilter': state}
        return self.__send_request("GET", self.__general, params=params)

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
        return self.__send_request("GET", self.__zipstream, params=params)

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

        params = {'action': 'update',
                  'PTZ.Various.V1.ReturnToOverview': seconds}
        return self.__send_request("GET", self.__general, params=params)

    def create_dynamic_overlay(self, text):
        """Create a dynamic overlay on the video

        Parameters
        ----------
        text: str
            Text to display on the dynamic overlay. i.e. %D %T:%f
        outline_color: str
            Outline of text. Can be white or black

        Returns
        -------
        bool
            API call was successfull
        """

        params = {"apiVersion": "1.0", "method": "addText",
                  "params": {"camera": 1, "text": text}}
        return self.__send_request("POST", self.__dynam_overlay, json=params)
    
    def change_dynamic_overlay_outline(self, identity, outline_color):
        """Change a dynamic overlay's outline color

        Parameters
        ----------
        identity: int
            Identity of the dynamic overlay to change. If you just have one then
            it is 1
        outline_color: str
            Outline of text. Can be white, or black

        Returns
        -------
        bool
            API call was successfull
        """
        
        params = {'apiVersion': '1.0', 'method': 'setText', 'params': {'identity': identity, 'textOLColor': outline_color}}
        return self.__send_request("POST", self.__dynam_overlay, json=params)

    def set_illumination_on(self, on=True):
        """Set illumination to on

        Args:
            on (bool, optional): Set illumination to on if True. Defaults to True.

        Returns
        -------
            bool
                API call was successfull
        """

        if on:
            method = 'enableLight'
        else:
            method = 'disableLight'

        params = {'apiVersion': '1.0', 'method': method,
                  'params': {'lightID': 'led0'}}
        return self.__send_request("POST", self.__light_control, json=params)

    @__try_catch
    def get_illumination_state(self):
        """Get illumination state of camera

        Returns
        -------
            bool
                API call was successfull
        """

        params = {'apiVersion': '1.0',
                  'method': 'getLightInformation', 'params': {}}
        return self.__send_request("POST", self.__light_control, check=False, json=params).json()['data']['items'][0]['enabled']

    @__try_catch
    def get_sd_card_filesystem(self):
        """Get SD Card filesystem

        Returns
        -------
            str
                Filesystem type
        """

        params = {'diskid': 'all'}
        response = self.__send_request(
            "GET", self.__list_sd, check=False, params=params)
        xmlFile = ET.fromstring(response.text)
        for tag in xmlFile.iter('disk'):
            if tag.attrib['diskid'] == 'SD_DISK':
                if tag.attrib['filesystem'] != 'vfat':
                    return 'ext4'
                else:
                    return 'vfat'

    def set_brightness(self, brightnessLevel):
        """Set brightness level

        Parameters
        ----------
        brightnessLevel: int
            Brightness of image used by camera. Can be an int from 0-100

        Returns
        -------
        bool
            API call was successfull
        """

        params = {'action': 'update',
                  'ImageSource.I0.Sensor.Brightness': brightnessLevel}
        return self.__send_request("GET", self.__general, params=params)

    def set_capture_mode(self, mode):
        """Set capture mode. Restarts the device upon completion

        Parameters
        ----------
        mode: int
            1 = 1080p 1920x1080 (16:9) @ 50/60 fps (no WDR), 0 = 1080p 1920x1080 (16:9) @ 25/30 fps

        Returns
        -------
        bool
            API call was successful
        """

        params = {'apiVersion': '1.0',
                  'method': 'setCaptureMode', 'channel': 0, 'captureModeId': mode}
        response = self.__send_request("POST", self.__capture_mode, json=params)
        self.restart()
        return response

    def get_system_ready(self):
        """Get if the system is ready 

        Returns
        -------
            requests.Response
                Data returned from API call
        """

        params = {'apiVersion': '1.0', 'method': 'systemready', 'params': {'timeout': 10}}
        return self.__send_request("POST", self.__system_ready, auth=False, check=False, json=params)
    
    @__try_catch
    def get_dynamic_overlays(self):
        """Get all dynamic overlays

        Returns
        -------
        requests.Response
            Response from API call
        """
        
        params = {'apiVersion': '1.0', 'method': 'list', 'params': {'camera': 1}}
        return self.__send_request('POST', self.__dynam_overlay, json=params, check=False).json()['data']['textOverlays']
    
    def restart(self):
        """Restart device

        Returns
        -------
        bool
            API call was successful
        """
        
        return self.__send_request("GET", self.__restart_cgi)
    
    def set_defog(self, on):
        """Set defog option

        Parameters
        ----------
        on: bool
            Wether to turn the defog effect on

        Returns
        -------
        bool
            API call was successful
        """
        
        params = {'action': 'update', 'ImageSource.IO.Sensor.Defog': on}
        return self.__send_request("GET", self.__general, params=params)
    
    def set_defog_strength(self, strength):
        """Set defog strength

        Parameters
        ----------
        strength: int
            Number between 0-100

        Returns
        -------
        bool
            API call was successful
        """
        
        params = {'action': 'update', 'ImageSource.IO.Sensor.DefogEffect': strength}
        return self.__send_request("GET", self.__general, params=params)
    
    def set_exposure_mode(self, mode):
        """Set exposure mode

        Parameters
        ----------
        mode: int
            0=auto, 1=hold, 2=flickerfree50, 3=flickerfree60, 4=flickerreduced50, 5=flickerreduced60

        Returns
        -------
        bool
            API call was successful
        """
        
        exposure_list = ['auto', 'hold', 'flickerfree50', 'flickerfree60', 'flickerreduced50', 'flickerreduced60']
        params = {'action': 'update', 'ImageSource.IO.Sensor.Exposure': exposure_list[mode]}
        return self.__send_request("GET", self.__general, params=params)
    
    def set_exposure_level(self, amount):
        """Set exposure level amount

        Parameters
        ----------
        amount: int
            Level amount for exposure setting

        Returns
        -------
        bool
            API call was successful
        """
        
        params = {'action': 'update', 'ImageSource.IO.Sensor.ExposureValue': amount}
        return self.__send_request("GET", self.__general, params=params)
    
    def set_exposure_zone(self, zone):
        """Set exposure zone

        Parameters
        ----------
        zone: int
            0=auto, 1=center, 2=upper, 3=lower, 4=left, 5=right, 6=spot, 7=custom

        Returns
        -------
        bool
            API call was successful
        """
        
        zone_list = ['auto', 'center', 'upper', 'lower', 'left', 'right', 'spot', 'custom']
        params = {'action': 'update', 'ImageSource.IO.Sensor.ExposureWindow': zone_list[zone]}
        return self.__send_request("GET", self.__general, params=params)

    def set_local_contrast(self, contrast_value):
        """Set local contrast

        Parameters
        ----------
        contrast_value: int
            Local contrast for camera video. Can be a value from 0-100

        Returns
        -------
        bool
            API call was successful
        """

        params = {'action': 'update', 'ImageSource.IO.Sensor.LocalContrast': contrast_value}
        return self.__send_request("GET", self.__general, params=params)

    def set_sharpness(self, sharpness_value):
        """Set sharpness for camera video

        Parameters
        ----------
        sharpness_value: int
            Sharpness value for camera video. Can be a value from 0-100

        Returns 
        -------
        bool
            API call was successful
        """

        params = {'action': 'update', 'ImageSource.IO.Sensor.Sharpness': sharpness_value}
        return self.__send_request("GET", self.__general, params=params)

    def set_eis(self, state):
        """Set Electronic Image Stabilization (EIS)

        Parameters
        ----------
        state: bool
            State of EIS. True=on False=off

        Returns
        -------
        bool
            API call was successful
        """

        stringState = "on" if state else 'off'
        params = {'action': 'update', 'ImageSource.IO.Sensor.Stabilizer': stringState}
        return self.__send_request("GET", self.__general, params=params)

    def set_stabilizer_margin(self, margin):
        """Set Stabilizer Margin for EIS

        Parameters
        ----------
        margin: int
            Margin to help EIS work better. Can be a value from 0-100

        Returns
        -------
        bool
            API call was successful
        """

        params = {'action': 'update', 'ImageSource.IO.Sensor.StabilizerMargin': margin}
        return self.__send_request("GET", self.__general, params=params)


    def set_white_balance(self, mode):
        """Set white balance

        Parameters
        ----------
        mode: int
            0=auto, 1=auto_outdoor, 2=hold, 3=manual, 4=fixed_outdoor1, 5=fixed_outdoor2,
            6=fixed_indoor, 7=fixed_flour1, 8=fixed_flour2

        Returns
        -------
        bool
            API call was successful
        """

        mode_list = ['auto', 'auto_outdoor', 'hold', 'manual', 'fixed_outdoor1', 'fixed_outdoor2', 'fixed_indoor', 'fixed_flour1', 'fixed_flour2']
        params = {'action': 'update', 'ImageSource.IO.Sensor.WhiteBalance': mode_list[mode]}
        return self.__send_request('GET', self.__general, params=params)

    def set_compression(self, value):
        """Set compression

        Parameters
        ----------
        value: int
            Compression value. Can be a number from 0-100

        Returns
        -------
        bool
            API call was successfull
        """

        params = {'action': 'update', 'Image.IO.Appearance.Compression': value}
        return self.__send_request("GET", self.__general, params=params)

    def set_resolution(self, value):
        """Set resolution

        Parameters
        ----------
        value: int
            0=1920x1080, 1=1280x720, 2=800x450, 3=480x270, 4=320x180

        Returns
        -------
        bool
            API call was successful
        """

        resolution_list = ['1920x1080', '1280x720', '800x450', '480x270', '320x180']
        params = {'action': 'update', 'Image.IO.Appearance.Resolution': resolution_list[value]}
        return self.__send_request("GET", self.__general, params=params)

    def set_zipstream_gop_mode_fixed(self, on=True):
        """Set the zipstream GOP mode to fixed

        Parameters
        ----------
        on: bool
            Turn GOP mode on

        Returns
        -------
        bool
            API call was successful
        """

        stringOnParameter = 'fixed' if on else 'dynamic'
        params = {'action': 'update', 'Image.IO.MPEG.ZGOPMode': stringOnParameter}
        return self.__send_request("GET", self.__general, params=params)

    def set_zipstream_fps_mode_fixed(self, on=True):
        """Set the zipstream FPS mode to fixed

        Parameters
        ----------
        on: bool
            Turn FPS mode on

        Returns
        -------
        bool
            API call was successful
        """

        stringOnParameter = 'fixed' if on else 'dynamic'
        params = {'action': 'update', 'Image.IO.MPEG.ZFPSMode': stringOnParameter}
        return self.__send_request('GET', self.__general, params=params)

    def set_max_gop_length(self, length):
        """Set max GOP length for Dynamic GOP

        Parameters
        ----------
        length: int
            Max GOP when dynamic GOP is selected. Can be a number from 1-1023

        Returns
        -------
        bool
            API call was successful
        """

        params = {'action': 'update', 'Image.IO.MPEG.ZMaxGopLength': length}
        return self.__send_request("GET", self.__general, params=params)

    def set_bitrate_control(self, mode):
        """Set bitrate cotrol

        Parameters
        ----------
        mode: int
            0=Variable, 1=Maximum, 2=Average, 3=Constant

        Returns
        -------
        bool
            API call was successful
        """

        mode_list = ['vbr', 'mbr', 'adr', 'cbr']
        params = {'action': 'update', 'root.Image.IO.RateControl.Mode': mode_list[mode]}
        return self.__send_request("GET", self.__general, params=params)

    def set_fps(self, fps):
        """Set Frames Per Second

        Parameters
        ----------
        fps: int
            frames per second. Can be a value from 0-30, 0=infinite

        Returns
        -------
        bool
            API call was successful
        """

        params = {'action': 'update', 'Image.IO.Stream.FPS': fps}
        return self.__send_request("GET", self.__general, params=params)

    def set_near_focus_limit(self, limit):
        """Set near focus limit

        Parameters
        ----------
        limit: int
            0=1m, 1=1.5m, 2=3m, 3=5m, 4=10m

        Returns
        -------
        bool
            API call was successful
        """

        limit_list = [1, 2381, 4762, 5714, 6428]
        params = {'action': 'update', 'PTZ.Limit.L1.MinFocus': limit_list[limit]}
        return self.__send_request("GET", self.__general, params=params)

    def set_adjustable_zoom_speed_on(self, on=True):
        """Set Adjustable zoom speed to on
        
        Parameters
        ----------
        on: bool
            Turns adjustable zoom speed on or off

        Returns
        -------
        bool
            API call was successful
        """

        stringOnParameter = 'true' if on else 'false'
        params = {'action': 'update', 'PTZ.UserAdv.U1.AdjustableZoomSpeedEnabled': on}
        return self.__send_request("GET", self.__general, params=params)

    def set_image_freeze_on(self, on=True):
        """Set Freeze image on PTZ to on

        Parameters
        ----------
        on: bool
            Turns image freeze on or off

        Returns
        -------
        bool
            API call was successful
        """

        stringOnParameter = 'on' if on else 'off'
        params = {'action': 'update', 'PTZ.UserAdv.U1.ImageFreeze': stringOnParameter}
        return self.__send_request("GET", self.__general, params=params)

    def set_proprtional_speed(self, speed):
        """Set max proportional speed

        Parameters
        ----------
        speed: int
            Proportional speed of camera. Can be a number from 1-1000

        Returns
        -------
        bool
            API call was successful
        """

        params = {'action': 'update', 'PTZ.Various.V1.MaxProportionalSpeed': speed}
        return self.__send_request("GET", self.__general, params=params)

    def set_proportional_speed_on(self, on=True):
        """Set proportional speed on

        Parameters
        ----------
        on: bool
            Enable proportional speed

        Returns
        -------
        bool
            API call was successful
        """

        stringOnParameter = 'true' if on else 'false'
        params = {'action': 'update', 'PTZ.Various.V1.ProportionalSpeedEnabled': stringOnParameter}
        return self.__send_request('GET', self.__general, params=params)

    def get_date_time(self):
        """Get date, time, and timezone
        
        Returns
        -------
        requests.Response
            API response
        """

        params = {"apiVersion": '1.0', 'method': 'getAll'}
        return self.__send_request('POST', self.__time, json=params, check=False)

    @__try_catch
    def get_time_zone(self):
        """Get time zone

        Parameters
        ----------
        str
            Current time zone
        """

        date_time = self.get_date_time().json()
        return date_time['data']['timeZone']

    def set_time_zone(self, time_zone):
        """Set time zone for camera
        
        Parameters
        ----------
        time_zone: str
            time zone for the camera. Use the get_date_time function to see all time zones

        Returns
        -------
        bool
            API call was successful
        """

        params = {'apiVersion': '1.0', 'method': 'setTimeZone', 'params': {'timeZone': time_zone}}
        return self.__send_request('POST', self.__time, json=params)

    @__try_catch
    def get_users(self):
        """Get camera users
        
        Returns
        -------
        list
            List of all the usernames on the camera
        """

        params = {'action': 'get'}
        return self.__send_request("POST", self.__users, data=params, check=False).text.split('\r\n')[-2].split('"')[1].split(',')

        

    def get_configuration_details(self):
        default_configs = (
            "ImageSource.I0.DayNight.IrCutFilter,"
            "ImageSource.I0.Sensor.Brightness,"
            "ImageSource.I0.Sensor.CaptureMode,"
            'ImageSource.I0.Sensor.ColorLevel'
            'ImageSource.I0.Sensor.Contrast'
            "ImageSource.I0.Sensor.Defog,"
            "ImageSource.I0.Sensor.DefogEffect," 
            "ImageSource.I0.Sensor.Exposure,"
            "ImageSource.I0.Sensor.ExposureValue,"
            "ImageSource.I0.Sensor.ExposureWindow,"
            "ImageSource.I0.Sensor.LocalContrast,"
            "ImageSource.I0.Sensor.Sharpness,"
            "ImageSource.I0.Sensor.Stabilizer,"
            "ImageSource.I0.Sensor.StabilizerMargin,"
            "ImageSource.I0.Sensor.WDR,"
            "ImageSource.I0.Sensor.WhiteBalance,"
            "Image.I0.Appearance.Compression,"
            "Image.I0.Appearance.Resolution,"
            "Image.I0.MPEG.ZFPSMode,"
            "Image.I0.MPEG.ZGOPMode,"
            "Image.I0.MPEG.ZMaxGopLength,"
            "Image.I0.MPEG.ZStrength,"
            "Image.I0.RateControl.Mode,"
            "Image.I0.Stream.FPS,"
            "PTZ.Limit.L1.MaxZoom,"
            "PTZ.Limit.L1.MinFocus,"
            "PTZ.UserAdv.U1.AdjustableZoomSpeedEnabled,"
            "PTZ.UserAdv.U1.ImageFreeze,"
            "PTZ.Various.V1.MaxProportionalSpeed,"
            "PTZ.Various.V1.ProportionalSpeedEnabled,"
            "PTZ.Various.V1.ReturnToOverview,"
            "Network.BootProto,"
            "Network.DNSServer1,"
            "Network.DNSServer2,"
            "Network.DefaultRouter,"
            "Network.IPAddress,"
            "Network.SubnetMask,"
            "Time.ObtainFromDHCP,"
            "Time.SyncSource"
        )

        overall_params = 'action=listdefinitions&listformat=xmlschema&responseformat=rfc&responsecharset=utf8&group=' + default_configs
        overall_response = self.__send_request("POST", self.__general, check=False, data=overall_params)
        all_configurations = self.__parse_response_text_to_xml(overall_response.text)
            
        # Get Illumination
        light_value = self.get_illumination_state()
        if light_value:
            all_configurations.append({'name': 'Light', 'value': light_value})
        # Get SD Card
        sd_value = self.get_sd_card_filesystem()
        if sd_value:
            all_configurations.append({'name': 'SD', 'value': sd_value})
        # Get Time Zone
        time_zone = self.get_time_zone()
        if time_zone:
            all_configurations.append({'name': 'timeZone', 'value': time_zone})
        # Get valorence user
        users = self.get_users()
        if 'valorence' in users:
            all_configurations.append({'name': 'AddValorence', 'value': 'valorence'})
        # Get Dynamic Overlays
        dynamic_overlays = self.get_dynamic_overlays()
        all_configurations.append({'name': 'DynamicOverlay', 'value': dynamic_overlays})
        # Get Default User
        all_configurations.append({'name': 'defaultUser', 'value': self.get_system_ready().json()['data']['needsetup']})
        return all_configurations

    @__try_catch
    def __parse_response_text_to_xml(self, response_text):
        parameterList = list()
        xmlFile = ET.fromstring(response_text)
        for parameter in xmlFile.iter("{http://www.axis.com/ParameterDefinitionsSchema}parameter"):
            parameterList.append(parameter.attrib)
        return parameterList