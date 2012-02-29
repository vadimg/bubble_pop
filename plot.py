import tornado.ioloop
import math
import matplotlib.pyplot as plt
from rates import getTreasuryData, getRealTreasuryData
from calcs import interpolate, makeForward, makeProb

YEARS = 7
PROB_SCALE = 5

rates = getTreasuryData()
rrates = getRealTreasuryData()
drates = dict(rates)
print rates
print rrates
print drates
inflations = []
for months, rate in rrates:
    inflation = drates[months] - rate
    inflations.append((months, inflation))
print inflations

rates = [inflations[0]]
for i in xrange(1, len(inflations)):
    m1, r1 = inflations[i-1]
    m2, r2 = inflations[i]
    d1 = m1/12.0
    d2 = m2/12.0
    rate = (((1+r2)**d2)/((1+r1)**d1))**(1/(d2-d1))-1
    rates.append((m2, rate))

xs = [x[0] for x in inflations]
ys = [x[1] for x in inflations]

plt.plot(xs, ys)
xs = [x[0] for x in rates]
ys = [x[1] for x in rates]
plt.plot(xs, ys)
plt.show()

