"""What the Patch checks (patch_checks.py) change: every value here must be the same again after each inner run"""
VALUE = "original"
MAPPING = {"key": "original"}
ENV = "TJ_PATCH_PROBE"


class Holder(object):

    @staticmethod
    def kind():
        return "original"


class Child(Holder):
    pass
