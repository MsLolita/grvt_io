import random
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import playwright.sync_api

from core.utils import shift_file, logger
from core.utils import file_to_list
from core import Grvt

from data.config import (
    REFERRAL_CODE, THREADS, CUSTOM_DELAY, EMAILS_FILE_PATH, PROXIES_FILE_PATH
)


class AutoReger:
    def __init__(self):
        self.emails_path: str = EMAILS_FILE_PATH
        self.proxies_path: str = PROXIES_FILE_PATH

        self.success: int = 0

    def get_accounts(self) -> list[tuple[str, str, str | None]]:
        emails: list[str] = file_to_list(self.emails_path)
        proxies: list[str] = file_to_list(self.proxies_path)

        min_accounts_len = len(emails)

        if not emails:
            logger.info("No emails!")
            exit()

        accounts = []

        for i in range(min_accounts_len):
            email, imap_pass = emails[i].split(":")[:2]
            accounts.append((email, imap_pass, proxies[i] if len(proxies) > i else None))

        return accounts

    def remove_account(self) -> None:
        shift_file(self.emails_path)
        shift_file(self.proxies_path)

    def start(self) -> None:
        Grvt.referral = REFERRAL_CODE

        accounts = self.get_accounts()

        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            executor.map(self.register, accounts)

        if self.success:
            logger.success(f"Successfully registered {self.success} accounts :)")
        else:
            logger.warning("No accounts registered :(")

    def register(self, account: tuple[str, str, str, str]) -> None:
        grvt = Grvt(*account)
        is_ok = False

        try:
            self.custom_delay()

            if grvt.register():
                logger.info(f"Registered {grvt.email}, wait for verify link...")
                verify_link = grvt.get_verify_link()

                is_ok = grvt.verify_email(verify_link)
        except playwright.sync_api.Error as e:
            logger.info(f"{grvt.email} | Can't bypass captcha")
            logger.debug(f"Error {e} | {traceback.format_exc()}")
        except Exception as e:
            logger.error(f"Error {e}")
            logger.debug(f"Error {e} | {traceback.format_exc()}")
        self.remove_account()

        if is_ok:
            grvt.logs("success", " | Registered")
            self.success += 1
        else:
            grvt.logs("fail", " | Couldn't register check out.logs")

    @staticmethod
    def custom_delay() -> None:
        if CUSTOM_DELAY[1] > 0:
            sleep_time = random.uniform(CUSTOM_DELAY[0], CUSTOM_DELAY[1])
            logger.info(f"Sleep for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

