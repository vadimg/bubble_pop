import tornado.ioloop
import tornado.web
import json
import os
from datetime import timedelta

from rates import getZeroData
from calcs import interpolate, makeForward, makeProb, makeFutureCurve

ratesCache = None

def mapzip(f, a):
    ret = []
    for x in a:
        y = f(x)
        if y is not None:
            ret.append((x, y))
    return ret

class RatesHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(json.dumps(ratesCache))

class ForwardRateHandler(tornado.web.RequestHandler):
    def get(self, months):
        months = int(months)

        lastMonth = ratesCache[-1][0]

        if months >= lastMonth:
            return self.write("")

        irates = interpolate(ratesCache)
        forward = makeForward(months, irates)

        x = range(1, lastMonth - months + 1)
        ret = mapzip(forward, x)

        self.write(json.dumps(ret))

class FutureRatesHandler(tornado.web.RequestHandler):
    def get(self, months):
        months = int(months)

        lastMonth = ratesCache[-1][0]

        if months >= lastMonth:
            return self.write("")

        irates = interpolate(ratesCache)
        forward = makeFutureCurve(months, irates)

        x = range(1, lastMonth - months + 1)
        ret = mapzip(forward, x)

        self.write(json.dumps(ret))


class ProbHandler(tornado.web.RequestHandler):
    def get(self):
        YEARS = 7
        PROB_SCALE = 5

        irates = interpolate(ratesCache)
        forward = makeForward(YEARS*12, irates)
        prob = makeProb(5, forward)

        lastMonth = ratesCache[-1][0]
        x = range(1, lastMonth - YEARS*12 + 1)
        ret = mapzip(prob, x)

        self.write(json.dumps(ret))

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html",
                    title="Will the tech bubble pop?",
                    api="pop_probability")

class HowHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("how.html", title="How I got these numbers :)")

class ZeroCurveHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("zero.html",
                    title="Zero Coupon Yield Curve",
                    api="zero_coupon_rates")

class ForwardCurveHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("forward.html",
                    title="Forward Yield Curve",
                    api="forward_rates/84")

class FutureCurveHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("future.html",
                    title="Future Yield Curve",
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
    td = timedelta(seconds=10)
    tornado.ioloop.IOLoop.instance().add_timeout(td, update_cache)

    def handle_resp(data):
        if data is None:
            return
        global ratesCache
        ratesCache = data
        if cb:
            cb()

    getZeroData(handle_resp)

if __name__ == "__main__":
    def listen():
        application.listen(8888)
    update_cache(listen)
    tornado.ioloop.IOLoop.instance().start()
