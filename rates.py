from datetime import datetime, timedelta
from xml.dom.minidom import parse
import re

from tornado.httpclient import AsyncHTTPClient
from BeautifulSoup import BeautifulSoup

def zeroYield(price, years):
    return (100.0/price)**(1.0/years)-1

def getZeroData(cb):
    now = datetime.now()

    url = 'http://online.wsj.com/mdc/public/page/2_3020-tstrips.html'

    def handle_resp(resp):
        if resp.error:
            return cb(None)

        html = resp.body
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

        return cb(ret)

    client = AsyncHTTPClient()
    client.fetch(url, handle_resp)

