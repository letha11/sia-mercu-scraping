from enum import Enum


class Flavor(Enum):
    DEV = "dev"
    PROD = "prod"

    def parse(value):
        if value == "dev":
            return Flavor.DEV
        elif value == "prod":
            return Flavor.PROD
        else:
            raise ValueError("Invalid flavor value: " + value)
    
    @property
    def is_dev(self):
        return self == Flavor.DEV

    @property
    def is_prod(self):
        return self == Flavor.PROD
