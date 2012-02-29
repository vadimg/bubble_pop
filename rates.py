from datetime import datetime, timedelta
from xml.dom.minidom import parse
import urllib2
import re

from tornado.httpclient import AsyncHTTPClient
from BeautifulSoup import BeautifulSoup

def getZeroData(cb):
    now = datetime.now()

    url = 'http://online.wsj.com/mdc/public/page/2_3020-tstrips.html'

    def handle_resp(resp):
        if resp.error:
            return cb(None)

        html = resp.body
        soup = BeautifulSoup(html)
        headings = soup.findAll('td', 'b14')[:2]

        date_str = soup.find('div', 'tbltime').findAll('span')[-1].string
        date_str = date_str.strip()
        update_date = datetime.strptime(date_str, '%A, %B %d, %Y')
        update_date = update_date.replace(hour=15)

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

        return cb(ret, update_date)

    client = AsyncHTTPClient()
    client.fetch(url, handle_resp)

def getTreasuryData():
    feed = 'http://data.treasury.gov/feed.svc/DailyTreasuryYieldCurveRateData?$filter=month(NEW_DATE)%20eq%20{0}%20and%20year(NEW_DATE)%20eq%20{1}'

    # TODO: handle case when 1st of month is on a weekend/holiday
    now = datetime.now()
    url = feed.format(now.month, now.year)

    dom = parse(urllib2.urlopen(url))

    return _parse_treasury_xml(dom)

def getRealTreasuryData():
    feed = 'http://data.treasury.gov/feed.svc/DailyTreasuryRealYieldCurveRateData?$filter=month(NEW_DATE)%20eq%20{0}%20and%20year(NEW_DATE)%20eq%20{1}'

    # TODO: handle case when 1st of month is on a weekend/holiday
    now = datetime.now()
    url = feed.format(now.month, now.year)

    dom = parse(urllib2.urlopen(url))

    return _parse_treasury_xml(dom)


def _parse_treasury_xml(dom):
    def getText(node):
            rc = []
            for node in node.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)
            return ''.join(rc)

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
            else:
                m = re.match(r'd:\wC_(\d+)((MONTH)|(YEAR))$', name)
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

def zeroYield(price, years):
    """
    @param price price of the bond
    @param years years to maturity
    @return yield of the zero-coupon bond
    """
    return (100.0/price)**(1.0/years)-1


