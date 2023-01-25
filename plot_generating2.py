

from threading import Thread
import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from itertools import count
import struct
# import pandas as pd


class serialPlot:
    x_buffer = []
    counter = count()

    def __init__(self, serialPort='COM10', serialBaud=115200, plotLength=100, dataNumBytes=2):
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.rawData = bytearray(dataNumBytes)
        self.data = collections.deque([0] * plotLength, maxlen=plotLength)
        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.plotTimer = 0
        self.previousTimer = 0
        # self.serialConnection = None
        # self.csvData = []

        print('Trying to connect to: ' + str(serialPort) +
              ' at ' + str(serialBaud) + ' BAUD.')
        try:
            self.serialConnection = serial.Serial(
                serialPort, serialBaud, timeout=4)
            print('Connected to ' + str(serialPort) +
                  ' at ' + str(serialBaud) + ' BAUD.')
        except:
            print("Failed to connect with " + str(serialPort) +
                  ' at ' + str(serialBaud) + ' BAUD.')

    def readSerialStart(self):
        if self.thread is None:
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            # Block till we start receiving values
            while self.isReceiving is False:
                time.sleep(0.1)

    def getSerialData(self, frame, lines, lineValueText, lineLabel, timeText):
        currentTimer = time.perf_counter()
        # the first reading will be erroneous
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)
        self.previousTimer = currentTimer
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
        # use 'h' for a 2 byte integer
        value, = struct.unpack('!h', self.rawData)
        # we get the latest data point and append it to our array
        self.data.append(value)
        # serialPlot.x_buffer.append(next(serialPlot.counter))
        lines.set_data(range(self.plotMaxLength), self.data)
        lineValueText.set_text('[' + lineLabel + '] = ' + str(value))
        # self.csvData.append(self.data[-1])

    def backgroundThread(self):    # retrieve data
        time.sleep(1.0)  # give some buffer time for retrieving data
        self.serialConnection.reset_input_buffer()
        while (self.isRun):
            # line = self.serialConnection.readline().decode('utf-8')[:-2]
            self.serialConnection.readinto(self.rawData)
            # self.rawData.append(float(line))
            self.isReceiving = True
            # print(self.rawData)

    def close(self):
        self.isRun = False
        self.thread.join()
        self.serialConnection.close()
        print('Disconnected...')
        # df = pd.DataFrame(self.csvData)
        # df.to_csv('/home/rikisenia/Desktop/data.csv')


def main():
    # portName = 'COM5'     # for windows users
    portName = 'COM10'
    baudRate = 115200
    maxPlotLength = 100
    dataNumBytes = 2        # number of bytes of 1 data point
    # initializes all required variables
    s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes)
    # starts background thread
    s.readSerialStart()

    # plotting starts below
    pltInterval = 50    # Period at which the plot animation updates [ms]
    xmin = 0
    xmax = maxPlotLength
    ymin = -(1)
    ymax = 300
    fig = plt.figure()
    ax = plt.axes(xlim=(xmin, xmax), ylim=(
        float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
    ax.set_title('Arduino Analog Read')
    ax.set_xlabel("time")
    ax.set_ylabel("AnalogRead Value")

    lineLabel = 'Potentiometer Value'
    timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
    lines = ax.plot([], [], label=lineLabel)[0]
    lineValueText = ax.text(0.50, 0.90, '', transform=ax.transAxes)
    anim = animation.FuncAnimation(fig, s.getSerialData, fargs=(
        lines, lineValueText, lineLabel, timeText), interval=pltInterval)    # fargs has to be a tuple

    plt.legend(loc="upper left")
    plt.show()

    s.close()


if __name__ == '__main__':
    main()
