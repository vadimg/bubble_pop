import datetime
import urllib2
from xml.dom.minidom import parse
import re


def getRateData():
    def getText(node):
            rc = []
            for node in node.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)
            return ''.join(rc)

    feed = 'http://data.treasury.gov/feed.svc/DailyTreasuryYieldCurveRateData?$filter=month(NEW_DATE)%20eq%20{0}%20and%20year(NEW_DATE)%20eq%20{1}'

    # TODO: handle case when 1st of month is on a weekend/holiday
    now = datetime.datetime.now()
    url = feed.format(now.month, now.year)
    #url = feed.format(3, 2000)

    dom = parse(urllib2.urlopen(url))

    entries = dom.getElementsByTagName('entry')

    maxdate = None
    maxdata = None
    for entry in entries:
        elems = entry.getElementsByTagName('content')[0].getElementsByTagName('m:properties')[0].childNodes

        ret = []
        for elem in elems:
            name = elem.nodeName
            if name == 'd:NEW_DATE':
                date = datetime.datetime.strptime(getText(elem), '%Y-%m-%dT%H:%M:%S')
            elif name.startswith('d:BC'):
                m = re.match(r'd:BC_(\d+)((MONTH)|(YEAR))$', name)
                if m:
                    months = int(m.group(1))
                    if m.group(2) == 'YEAR':
                        months *= 12
                    try:
                        rate = float(getText(elem))
                        ret.append((months, rate))
                    except ValueError:
                        pass

        if maxdate is None or maxdate < date:
            maxdata = ret
            maxdate = date

    return maxdata

def interpolate(rates):
    def get(month):
        if month < rates[0][0]:
            return None

        for m2, r2 in rates:
            if m2 == month:
                return r2
            elif m2 > month:
                # interpolate
                f = lambda x: (r2-r1)/(m2-m1)*(x-m1) + r1
                return f(month)
            m1, r1 = m2, r2
    return get

def makeForward(months, irates):
    def get(month):
        d1 = month/12.0
        d2 = (month + months)/12.0
        r1 = irates(month)
        r2 = irates(month + months)

        if r1 is None or r2 is None:
            return None

        return (((1.0+r2)**d2)/((1.0+r1)**d1))**(1.0/(d2-d1)) - 1
    return get


rates = getRateData()
irates = interpolate(rates)
forward = makeForward(10*12, irates)

import matplotlib.pyplot as plt
x = range(1,361)
y = map(irates, x)
vals = zip(x,y)

fig = plt.figure()
plt.plot(x, y)
x = range(1,20*12+1)
plt.plot(x, map(forward, x))
plt.show()

