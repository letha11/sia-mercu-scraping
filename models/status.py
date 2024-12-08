from enum import Enum

class Status(Enum):
    SUCCESS = 1
    UNAUTHORIZED = 2
    FAILURE = 3
    RELOGIN_NEEDED = 4

