import random
import secrets
import string
from random import choice

import requests
import tls_client
import pyuseragents
from playwright.sync_api import sync_playwright

from core.utils import str_to_file, logger
from string import ascii_lowercase, digits

from core.utils import MailUtils
from core.utils.custom_faker import CustomFaker
from data.config import MOBILE_PROXY, MOBILE_PROXY_CHANGE_IP_LINK


class Grvt(MailUtils, CustomFaker):
    referral = None

    def __init__(self, email: str, imap_pass: str, proxy: str = None):
        CustomFaker.__init__(self)
        super().__init__(email, imap_pass)

        self.proxy = Grvt.get_proxy(proxy)

        self.password = Grvt.generate_strong_password(random.randint(8, 12))

        self.headers = {
            'authority': 'edge.grvt.io',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://grvt.io',
            'referer': 'https://grvt.io/',
            'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': pyuseragents.random(),
        }

        self.session = tls_client.Session(
            client_identifier="chrome112",
            random_tls_extension_order=True
        )

        self.session.headers.update(self.headers)
        if proxy:
            self.session.proxies.update({
                'http': f"http://{proxy}",
                'https': f"http://{proxy}",
            })

        self.page = None

    @staticmethod
    def get_proxy(proxy: str):
        if MOBILE_PROXY:
            Grvt.change_ip()
            proxy = MOBILE_PROXY

        if proxy is not None:
            return f"http://{proxy}"

    @staticmethod
    def change_ip():
        requests.get(MOBILE_PROXY_CHANGE_IP_LINK)

    def get_browser(self):
        proxy = None
        if self.proxy:
            server = f"http://{self.proxy.split('@')[1]}"
            username, password = self.proxy.split('@')[0].split(':')
            proxy = {"server": server, "username": username, "password": password}

        return self.p.firefox.launch(
            headless=False,
            ignore_default_args=["--enable-automation"],
            args=[
                '--start-maximized',
                "--disable-blink-features=AutomationControlled"
            ],
            chromium_sandbox=False,
            proxy=proxy
        )

    def register(self):
        with sync_playwright() as self.p:
            browser = self.get_browser()
            self.page = browser.new_page(no_viewport=True)

            self.page.goto("https://grvt.io/exchange/sign-up/retail", referer="https://google.com/", timeout=60000)

            self.fill_form()

            browser.close()
        return True

    def perform_action(self, locator, action, value=None, wait_timeout=1000):
        element = self.page.locator(locator)
        if action == "fill":
            element.fill(value)
        elif action == "click":
            element.click()
        self.page.wait_for_timeout(wait_timeout * random.uniform(1, 1.5))

    def fill_form(self):
        self.perform_action("[id='\:r0\:']", "fill", self.email)
        self.perform_action("#referralCode", "fill", Grvt.referral)
        self.perform_action("[type=submit]", "click")
        self.perform_action("[id='\:r4\:']", "fill", self.name)
        self.perform_action("[id='\:r5\:']", "fill", self.last_name)
        self.perform_action("[id='\:r6\:']", "fill", self.password)
        self.perform_action("[id='\:r7\:']", "fill", self.password)
        self.perform_action(".style_CheckboxContainer__A83Or svg", "click")
        self.perform_action("button[type=submit]", "click")

        self.page.locator(".heading-10").wait_for(timeout=7000)

    def get_verify_link(self):
        result = self.get_msg(subject='GRVT: Confirm New Account', from_='no-reply@grvt.io',
                              to=self.email, limit=2)

        return result["msg"].split("<td><a href=")[1].split(' target="_blank" ')[0]

    def verify_email(self, verify_link: str):
        url = (verify_link.replace("grvt.io", "edge.grvt.io")
               .replace("&#61;", "=").replace("%3D%3D", "=="))

        response = self.send_request("get", url)

        return response.json()["status"] == "success"

    def send_request(self, method, url, headers=None, json_data=None, params=None, data=None, allow_redirects=True):
        if not headers:
            headers = self.headers.copy()

        endpoint = url.split('/')[-1]

        for _ in range(4):
            try:
                resp = getattr(self.session, method)(url, headers=headers, json=json_data, params=params,
                                                     data=data, allow_redirects=allow_redirects
                                                     )

                logger.debug(f"{resp.status_code} | {endpoint} | {resp.text}")
                if resp.status_code == 200:
                    return resp

            except Exception as e:
                logger.error(f"Request Error: {e}")

        raise Exception(f"Failed to send request | {endpoint}")

    def logs(self, file_name: str, msg_result: str = ""):
        log_message = f"{self.email}{msg_result}"
        getattr(logger, "success" if file_name == "success" else "error")(log_message)

        str_to_file(f"./logs/{file_name}.txt", f"{self.email}|{self.proxy}")

    @staticmethod
    def generate_password(k=10):
        return ''.join([choice(ascii_lowercase + digits) for i in range(k)])

    @staticmethod
    def generate_strong_password(k=10):
        while True:
            password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(k)) + random.choice(
                ["!", "@", "#", "$", "%", "^", "&", "*"])
            if (sum(c.islower() for c in password) >= 1
                    and sum(c.isupper() for c in password) >= 1
                    and sum(c.isdigit() for c in password) >= 1):
                return password
