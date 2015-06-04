#!/usr/bin/env python

from pytx import ThreatExchangeMember
from pytx.vocabulary import ThreatExchangeMember as tem


def run():
    results = ThreatExchangeMember.objects()
    for result in results:
        print '"%s","%s"' % (result.get(tem.NAME),
                             result.get(tem.ID))


def main():
    run()

if __name__ == '__main__':
    main()
