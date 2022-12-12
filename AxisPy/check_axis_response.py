import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import json


def check_response(response):
    if response:
        if response.text == "OK":
            return True
        elif check_response_as_xml(response):
            return True
        elif check_response_as_html(response):
            return True
        elif check_ntp_response(response):
            return True
        elif check_dynamic_overlay(response):
            return True
        elif check_illumination(response):
            return True
        elif check_capture_mode(response):
            return True
        elif check_get_dynamic_overlays(response):
            return True
        elif check_restart(response):
            return True
        elif check_time_response(response):
            return True
        elif check_system_ready(response):
            return True
        else:
            return False

def try_json(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return False
        except json.decoder.JSONDecodeError:
            return False
    return wrapper

@try_json
def check_ntp_response(response):

    jsonResponse = response.json()
    jsonResponse['apiVersion']
    jsonResponse['data']
    if jsonResponse['method'] == 'setNTPClientConfiguration':
        return True
    return False

@try_json
def check_time_response(response):

    jsonResponse = response.json()
    if jsonResponse['method'] == 'getAll':
        if type(jsonResponse['data']) == type(dict()):
            return True
    return False

@try_json
def check_dynamic_overlay(response):

    jsonResponse = response.json()
    if jsonResponse['method'] == 'setText':
        if type(jsonResponse['data']) == type(dict()):
            return True
    return False

@try_json    
def check_illumination(response):

    jsonResponse = response.json()
    if jsonResponse['method'] == 'disableLight' or jsonResponse['method'] == 'enableLight':
        if type(jsonResponse['data']) == type(dict()):
            return True
    return False

@try_json
def check_capture_mode(response):

    jsonResponse = response.json()
    if jsonResponse['method'] == 'setCaptureMode':
        if type(jsonResponse['data']) == type(dict()):
            return True
    return False

@try_json
def check_get_dynamic_overlays(response):

    jsonResponse = response.json()
    if jsonResponse['method'] == 'list':
        if type(jsonResponse['data']['textOverlays']) == type(list()):
            return True

    return False

@try_json
def check_system_ready(response):
    jsonResponse = response.json()
    if jsonResponse['method'] == 'systemready':
        if isinstance(jsonResponse['data'], dict):
            return True
        
    return False 

def check_response_as_xml(response):
    try:
        xmlResponse = ET.fromstring(response.text)
        print(xmlResponse.tag)
        if xmlResponse.find('./Success') or xmlResponse.find('./{http://www.axis.com/vapix/http_cgi/zipstream1}Success'):
            return True
        elif xmlResponse.find('./Error'):
            return False
    except ParseError as e:
        print("Parse Error", e)
        return False

def check_response_as_html(response):
    try:
        parsingHtml = BeautifulSoup(response.text, 'html.parser')
        body_string = parsingHtml.find('head').string
        print(body_string)
        if "Created account" in body_string:
            return True
            return False
    except AttributeError:
        print("HTML Parse Error")
        return False
    except TypeError:
        return False

def check_restart(response):
    try:
        parsingHTML = BeautifulSoup(response.text, 'html.parser')
        if parsingHTML.find('[http-equiv]'):
            return True
        else:
            return False
    except AttributeError:
        return False
