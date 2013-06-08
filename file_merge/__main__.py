import sys
from .utils import verbose, ERROR


def main(args):
    if len(args) != 2:
        verbose("%s PATH" % args[0], ERROR)
        return 1
    p3b(args[1])


main(sys.argv)
