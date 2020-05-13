import ast
import traceback
import click

from colorama import Fore, Style
from test_junkie.constants import Undefined


class PythonLiteralOption(click.Option):

    def type_cast_value(self, ctx, value):
        try:
            if value is not None and not isinstance(value, Undefined):
                return ast.literal_eval(value)
            return value
        except:
            print("shit")
            print(traceback.format_exc())
            raise click.BadParameter(value)


class Color:

    __INITIALIZED = False

    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    def __init__(self):

        pass

    @staticmethod
    def __initialize():
        if not Color.__INITIALIZED:
            import colorama
            colorama.init()
            Color.__INITIALIZED = True

    @staticmethod
    def format_string(value, color):
        Color.__initialize()
        colors = {"red": Fore.RED, "green": Fore.GREEN, "yellow": Fore.YELLOW, "blue": Fore.BLUE}
        return "{style}{color}{value}{reset}".format(style=Style.BRIGHT, color=colors[color],
                                                     value=value, reset=Style.RESET_ALL)

    @staticmethod
    def print_traceback(trace=None):
        Color.__initialize()
        print(Style.BRIGHT + Fore.RED)
        if trace is None:
            print(traceback.format_exc())
        else:
            print(trace)
        print(Style.RESET_ALL)

    @staticmethod
    def format_bold_string(value):
        Color.__initialize()
        return "{bold}{value}{end}".format(bold=Color.BOLD, value=value, end=Color.END)
