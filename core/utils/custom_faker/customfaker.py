import random

import names


class CustomFaker:
    def __init__(self):
        self.name, self.last_name = names.get_full_name().lower().split(" ")

        self.last_username = None

    def __get_name_username(self):
        username_list = [self.name, self.last_name]
        random.shuffle(username_list)

        return "_".join(username_list)
