# banking/__init__.py
from .millennium.parser import MillenniumParser
from .bpi.parser import BPIParser

BANK_REGISTRY = {
    "millennium": MillenniumParser(),
    "bpi": BPIParser(),
}
