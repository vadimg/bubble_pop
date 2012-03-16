import json
import os
from datetime import timedelta
from collections import namedtuple

import tornado.ioloop
import tornado.web
import asyncmongo

from rates import getZeroData
from calcs import interpolate, makeForward, makeProb, makeFutureCurve

Cache = namedtuple('Cache', ['rates', 'updated'])

cache = Cache(rates=None, updated=None)

def mapzip(f, a):
    ret = []
    for x in a:
        y = f(x)
        if y is not None:
            ret.append((x, y))
    return ret

class RatesHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(json.dumps(cache.rates))

class ForwardRateHandler(tornado.web.RequestHandler):
    def get(self, months):
        months = int(months)

        lastMonth = cache.rates[-1][0]

        if months >= lastMonth:
            return self.write("")

        irates = interpolate(cache.rates)
        forward = makeForward(months, irates)

        x = range(1, lastMonth - months + 1)
        ret = mapzip(forward, x)

        self.write(json.dumps(ret))

class FutureRatesHandler(tornado.web.RequestHandler):
    def get(self, months):
        months = int(months)

        lastMonth = cache.rates[-1][0]

        if months >= lastMonth:
            return self.write("")

        irates = interpolate(cache.rates)
        forward = makeFutureCurve(months, irates)

        x = range(1, lastMonth - months + 1)
        ret = mapzip(forward, x)

        self.write(json.dumps(ret))


class ProbHandler(tornado.web.RequestHandler):
    def get(self):
        YEARS = 7
        PROB_SCALE = 5

        irates = interpolate(cache.rates)
        forward = makeForward(YEARS*12, irates)
        prob = makeProb(5, forward)

        lastMonth = cache.rates[-1][0]
        x = range(1, lastMonth - YEARS*12 + 1)
        ret = mapzip(prob, x)

        self.write(json.dumps(ret))

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html",
                    title="Will the tech bubble pop?",
                    updated=cache.updated,
                    api="pop_probability")

class HowHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("how.html",
                    title="How I got these numbers :)",
                    updated=cache.updated)

class ZeroCurveHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("zero.html",
                    title="Zero Coupon Yield Curve",
                    updated=cache.updated,
                    api="zero_coupon_rates")

class ForwardCurveHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("forward.html",
                    title="Forward Yield Curve",
                    updated=cache.updated,
                    api="forward_rates/84")

class FutureCurveHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("future.html",
                    title="Future Yield Curve",
                    updated=cache.updated,
                    api="future_rates/12")


application = tornado.web.Application(
    [
        (r"/", IndexHandler),
        (r"/how", HowHandler),
        (r"/zero_coupon_curve", ZeroCurveHandler),
        (r"/forward_curve", ForwardCurveHandler),
        (r"/future_curve", FutureCurveHandler),
        (r"/api/zero_coupon_rates", RatesHandler),
        (r"/api/forward_rates/(\d+)", ForwardRateHandler),
        (r"/api/future_rates/(\d+)", FutureRatesHandler),
        (r"/api/pop_probability", ProbHandler),
    ],
    static_path=os.path.join(os.path.dirname(__file__), "static"),
    template_path=os.path.join(os.path.dirname(__file__), "templates"),
)

def update_cache(cb=None):
    td = timedelta(minutes=30)
    tornado.ioloop.IOLoop.instance().add_timeout(td, update_cache)

    def handle_resp(data, update_date):
        if data is None:
            return
        global cache

        db = asyncmongo.Client(pool_id='mydb', host='127.0.0.1', port=27017, maxcached=10, maxconnections=50, dbname='interest_rates_hist')

        def mongo_find_resp(response, error):
            if error:
                print error
                return

            # do nothing if data already exists for this time
            if response:
                return

            def check_output(response, error):
                if error:
                    print error

            db.zero_coupon.insert({
                'time': update_date,
                'data': data
            }, callback=check_output)

        db.zero_coupon.find({'time': update_date}, callback=mongo_find_resp)

        cache = Cache(rates=data, updated=update_date)

        if cb:
            cb()

    getZeroData(handle_resp)

if __name__ == "__main__":
    def listen():
        application.listen(3001)
    update_cache(listen)
    tornado.ioloop.IOLoop.instance().start()
