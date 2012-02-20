from datetime import datetime, timedelta
import urllib2
from xml.dom.minidom import parse
import re

from BeautifulSoup import BeautifulSoup

def zeroYield(price, years):
    return (100.0/price)**(1.0/years)-1

def getZeroData():
    now = datetime.now()

    url = 'http://online.wsj.com/mdc/public/page/2_3020-tstrips.html'

    html = urllib2.urlopen(url).read()
    soup = BeautifulSoup(html)
    headings = soup.findAll('td', 'b14')[:2]
    data = {}
    for item in headings:
        trs = item.parent.findNextSiblings('tr')
        for tr in trs:
            tds = tr.findAll('td')
            if len(tds) != 5:
                break
            date = datetime.strptime(tds[0].string, '%Y %b %d')
            price = float(tds[2].string)
            daysBetween = (date - now).days
            years = daysBetween/365.0
            months = int(round(years*12))
            if months == 0:
                continue

            zyield = 100*zeroYield(price, years)

            data.setdefault(months, []).append(zyield)

    ret = []
    for months, yields in data.iteritems():
        avgyield = round(sum(yields)/len(yields), 2)
        ret.append((months, avgyield))

    ret.sort(key=lambda x: x[0])

    return ret

def getTreasuryData():
    def getText(node):
            rc = []
            for node in node.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)
            return ''.join(rc)

    feed = 'http://data.treasury.gov/feed.svc/DailyTreasuryYieldCurveRateData?$filter=month(NEW_DATE)%20eq%20{0}%20and%20year(NEW_DATE)%20eq%20{1}'

    # TODO: handle case when 1st of month is on a weekend/holiday
    now = datetime.now()
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
                date = datetime.strptime(getText(elem), '%Y-%m-%dT%H:%M:%S')
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


