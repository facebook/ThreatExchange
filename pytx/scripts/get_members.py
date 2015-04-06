#!/usr/bin/env python

from pytx import init
from pytx import ThreatExchangeMember
from pytx.vocabulary import ThreatExchangeMember as tem

app_id = '<your-app-id>'
app_secret = '<your-app-secret>'

init(app_id, app_secret)

results = ThreatExchangeMember.objects()
for result in results:
    print '"%s","%s"' % (result.get(tem.NAME),
                         result.get(tem.ID))
