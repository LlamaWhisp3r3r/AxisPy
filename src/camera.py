from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from requests.auth import HTTPDigestAuth
from selenium import webdriver
import requests
import json
import time

class AxisConfigure:

    def __init__(self, ip, username, password):
        self.ip = ip
        self.__username = username
        self.__password = password
        self.__dynam_overlay = 'dynamicoverlay/dynamicoverlay.cgi'
        self.__general = 'param.cgi'
        self.__ptz = 'com/ptz.cgi'
        self.__time = 'time.cgi'
        self.__ntp = 'ntp.cgi'
        self.__users = 'pwdgrp.cgi'
        self.__device_info = 'basicdeviceinfo.cgi'
        self.__sd_card = 'disks/properties/setrequiredfs.cgi'
        self.__zipstream = 'zipstream/setstrength.cgi'
        self.__url = 'http://{}/axis-cgi/{}'

    def __debug(self, message):
        print("[DEBUG]\t" + message)

    def config(self):
        pass

    def __send_request(self, parameters, endpoint, auth=True):
        formatted_url = self.__url.format(self.ip, endpoint)
        response = None
        if auth:
            digest_auth = HTTPDigestAuth(self.__username, self.__password)
            response = requests.post(formatted_url, auth=digest_auth, json=parameters)
        else:
            response = requests.post(formatted_url, json=params)
        return response

    def get_device_information(self):
        params = {'apiVersion': '1.0', 'context': 'Client defined request ID', 'method': 'getAllProperties'}
        response = self.__send_request(params, self.__device_info)
        return response.text

    def get_serial_and_product(self):
        response = self.get_device_information()
        # SerialNumber and ProductName
        SN = response['data']['propertyList']['SerialNumber']
        PN = response['data']['propertyList']['ProdShortName']
        return SN, PN

    def update_ip(self, new_ip='192.168.1.3', gateway='192.168.1.1', dnsserver_1='8.8.8.8', dnsserver_2='192.168.1.1'):
        params = {'action': 'update', 'Network.BootProto': 'none', 'Network.Resolver.ObtainFromDHCP': 'no', 'Network.IPAddress': new_ip, 'Network.DefaultRouter': gateway, 'Network.DNSServer1': dnsserver_1, 'Network.DNSServer2': dnsserver_2}
        response = self.__send_request(params, self.__general)
        return response.text

    def update_sd_card(self):
        # --- Flip storage switch ---
        params = {'schemaversion': 1, 'diskid': 'SD_DISK', 'filesystem': 'ext4'}
        response = self.__send_request(params, self.__sd_card)
        return response.text

    def update_user(self):
        params = {'action': 'add', 'user': 'valorence', 'pwd': 'Covert1234', 'grp': 'users', 'strict_pwd': 1, 'sgrp': 'viewer:operator:admin:ptz'}
        response = self.__send_request(params, self.__users)
        return response.text

    def update_ntp_server(self):
        params = {"apiVersion":"1.1","method":"setNTPClientConfiguration","params":{"enabled":True,"serversSource":"static","staticServers":["ntp.axis.com"]}}
        response = self.__send_request(params, self.__ntp)
        return response.text

    def update_ntp_dhcp_mode(self, dhcp=False):
        params = {'action': 'update', 'Time.ObtainFromDHCP': 'no'}
        response = self.__send_request(params, self.__general)
        return response.text

    def update_zoom_limit(self):
        params = {'action': 'update', 'PTZ.Limit.L1.MaxZoom': '10909'} # 10909 seems to be the first digital option, and 9999 is the last mechanical option
        response = self.__send_request(params, self.__general)
        return response.text

    def update_wdr(self):
        params = {'action': 'update', 'ImageSource.I0.Sensor.WDR': 'on'}
        resoponse = self.__send_request(params, self.__general)
        return response.text

    def update_ir_cut_filter(self):
        params = {'action': 'update', 'ImageSource.I0.DayNight.IrCutFilter': 'yes'} # yes=on, no=off, auto=auto
        response = self.__send_request(params, self.__general)
        return response.text

    def update_zipstream(self):
        params = {'strength': '30'} # 10=low, 20=medium, 30=high, 40=higher, 50=extreme
        response = self.__send_request(params, self.__zipstream)
        return response.text

    def update_time_to_home(self):
        params = {'action': 'update', 'PTZ.Various.V1.ReturnToOverview': '1500'}
        response = self.__send_request(params, self.__general)
        return response.text

    def update_dynamic_overlay(self):
        params = {"apiVersion":"1.0","method":"addText","params":{"camera":1,"text":"%D %T:%f"}}
        response = requests.post(url.format(IP, dynam), auth=HTTPDigestAuth("root", "Avscle2010"), json=params)
        return response.text

    def factory_login(self):
        # Should be able to do this with requests instead of selenium
        handssl = Options()
        handssl.accept_untrusted_certs = True
        handssl.assume_untrusted_cert_issuer=False
        service = Service('geckodriver.exe')
        driver = webdriver.Firefox(service=service, options=handssl)
        driver.get("http://" + IP)

        time.sleep(15)
        passfield = driver.find_element(By.ID, 'rootPwd1')
        passfield2 = driver.find_element(By.ID, 'rootPwd2')
        passbut = driver.find_element(By.ID, 'wizardSubmitBtn')
        password = 'Avscle2010'
        passfield.send_keys(password)
        time.sleep(1)
        passfield2.send_keys(password)
        time.sleep(1)
        passbut.click()
        time.sleep(3)
        try:
            driver.quit()
        except Exception:
            pass
