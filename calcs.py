import math
import bisect

def interpolate(rates):
    keys = [r[0] for r in rates]

    def get(month):
        if month > rates[-1][0]:
            return None

        # index of value less than or equal to
        i = bisect.bisect_right(keys, month) - 1
        if i < 0:
            return None

        m1, r1 = rates[i]
        if m1 == month:
            return r1
        else:
            # interpolate
            m2, r2 = rates[i+1]
            f = lambda x: (r2-r1)/(m2-m1)*(x-m1) + r1
            return f(month)

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

def makeFutureCurve(months, irates):
    def get(month):
        d1 = months/12.0
        d2 = (month + months)/12.0
        r1 = irates(months)
        r2 = irates(month + months)

        if r1 is None or r2 is None:
            return None

        return (((1.0+r2)**d2)/((1.0+r1)**d1))**(1.0/(d2-d1)) - 1
    return get


def makeProb(s, forward):
    """s is the scale factor, forward is the forward curve function"""
    def get(month):
        r = forward(month)
        if r is None:
            return None
        return 1-math.e**(-(r/s)**2)
    return get

