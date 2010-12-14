import time
from math import sqrt

class TimeSample():
    
    def __init__(self, name="", org=False):
        self.start_time = -1
        self.stop_time = -1
        # Time elapsed in test. Faster the time, higher per second
        # value, or lower elapsed time higher per second value.
        self.value = None
        self.name = name
        # Number of itterations used to sample. Higher the value,
        # higher per second time.
        self.iterations = 1;
        self.org = org
        self.start()

    def start(self):
        self.start_time = time.time()
    
    def stop(self):
        self.stop_time = time.time()
    
    def diff(self):
        self.value = self.stop_time - self.start_time

    def sample(self, iterations=1):
        self.stop()
        self.iterations = iterations
        return self

    def add(self, sample):
        self.sample()

    def __perSecond(self):
        if (self.value == 0): return 1.
        return self.iterations//self.value

    def data(self):
        if not self.org:
            out = self.name + "\t"  + str(round(self.value,5)) + "\t" + str(round(self.__perSecond(),1)) + "\n"
        else:
            out = "| " + self.name + "\t|"  + str(round(self.value,5)) + "\t|" + str(round(self.__perSecond(),1)) + "|\n"
        return out

    def header(self):
        out = "Time test sampled over " + str(self.iterations) + " iterations:\n"
        out += "Test" + "\t" + "Time value * " + str(self.counter) + "\t" + "Oper/s\n"

class StatisticSample(TimeSample):

    def __init__(self, name, org=False):
        TimeSample.__init__(self, name, org)
        self.samples = list()
        self.sum = 0
        # All samples in the sample have equal number of iterations
        self.iterations = 0
        self.counter = 0
        self.mean = None
        self.deviation = None
        self.current = None

    def sample(self, iterations=1):
        self.__calculate()
        return self

    def new(self):
        self.current = StatisticSample(self.name)
        self.current.start()

    def add(self, iterations=1):
        self.current.stop()
        self.current.diff()
        self.iterations = iterations
        self.samples.append(self.current)
        self.sum += self.current.value
        self.counter += 1

    def __perSecond(self):
        return self.iterations/self.mean

    def __calculate(self):
        self.mean = self.sum/self.counter
        self.deviation = self.__deviation()

    def __deviation(self):
        _sq = 0
        for s in self.samples:
            _sq += pow((s.value - self.mean),2)
        return sqrt(_sq/self.counter)

    def __devPercent(self):
        return round(self.deviation/self.mean*100,2)
    
    def data(self):
        if not self.org:
            out = self.name + "\t" + str(round(self.mean,5)) + "+-" + str(self.__devPercent()) + "%\t\t" + str(round(self.__perSecond(),1)) + "\n"
        else:
            out = "| " + self.name + "\t|" + str(round(self.mean,5)) + "+-" + str(self.__devPercent()) + "%\t\t|" + str(round(self.__perSecond(),1)) + "|\n"
        return out

    def header(self):
        out = "Time test on " + str(self.counter) + " samples, each with " + str(self.iterations) + " iterations:\n"
        out += "\tTest" + "\t\t" + "Time value * " + str(self.iterations) + "+-std." + "\t" + "Oper/s\n"
        return out

class TimeSeries():

    def __init__(self, name, org=False):
        self.series = list()
        self.name = name
        self.current = None
        self.commonHeader = True
        self.org = org

    def start(self, name=""):
        self.current = TimeSample(name, self.org)

    def stop(self, iterations=1):
        self.series.append(self.current.sample(iterations))

    def toString(self):
        out = "Time test series: " + self.name + "\n"
        if self.commonHeader: 
            out += self.series[0].header()
        for s in self.series:
            if self.commonHeader == False: 
                out += s.header()
            out += s.data()
        return out


class StatisticTimeSeries(TimeSeries):
    
    def __init__(self, name, org=False):
        TimeSeries.__init__(self, name, org)
        self.temp = None
        self.org = org

    def start(self, name=""):
        self.current = StatisticSample(name, self.org)

    def stop(self):
        self.series.append(self.current.sample())

    def new(self):
        self.current.new()

    def add(self, iterations=1):
        self.current.add(iterations)

