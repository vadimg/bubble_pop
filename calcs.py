import math

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

def makeProb(s, forward):
    """s is the scale factor, forward is the forward curve function"""
    def get(month):
        r = forward(month)
        if r is None:
            return None
        return 1-math.e**(-(r/s)**2)
    return get

