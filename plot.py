import math
import matplotlib.pyplot as plt
from rates import getZeroData
from calcs import interpolate, makeForward, makeProb

YEARS = 10
PROB_SCALE = 5


rates = getZeroData()

irates = interpolate(rates)
forward = makeForward(YEARS*12, irates)
prob = makeProb(PROB_SCALE, forward)

x = range(1,20*12+1)
plt.plot(x, map(prob, x))
plt.show()

