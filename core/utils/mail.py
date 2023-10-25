import time
from typing import Optional, Dict

from imap_tools import MailBox, AND
from loguru import logger


class MailUtils:
    def __init__(
            self,
            email: str,
            imap_pass: str
    ) -> None:

        self.email: str = email
        self.imap_pass: str = imap_pass
        self.domain: str = self.parse_domain()

    def get_msg(
            self,
            to: Optional[str] = None,
            subject: Optional[str] = None,
            from_: Optional[str] = None,
            seen: Optional[bool] = None,
            limit: Optional[int] = None,
            reverse: bool = True,
            delay: int = 60
    ) -> Dict[str, any]:
        with MailBox(self.domain).login(self.email, self.imap_pass) as mailbox:
            for _ in range(delay // 3):
                try:
                    for msg in mailbox.fetch(AND(to=to, from_=from_, seen=seen), limit=limit, reverse=reverse):

                        if subject is not None and msg.subject != subject:
                            continue

                        logger.success(f'{self.email} | Successfully received msg: {msg.subject}')
                        return {"success": True, "msg": msg.html}
                except Exception as error:
                    logger.error(f'{self.email} | Unexpected error when getting code: {str(error)}')
                # logger.error(f'{self.email} | No message received')
                time.sleep(3)
        logger.error(f'{self.email} | No message received')
        return {"success": False, "msg": "Didn't find msg"}

    def parse_domain(self) -> str:
        domain: str = self.email.split("@")[-1]

        if "hotmail" in domain or "live" in domain:
            domain = "outlook.com"
        elif "firstmail" in domain:
            domain = "firstmail.ltd"

        return f"imap.{domain}"
