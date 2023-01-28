

from threading import Thread
import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation


class serialPlot:

    def __init__(self, serialPort='COM10', serialBaud=115200, plotLength=100, dataNumBytes=2):
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.rawData = ''
        self.data = collections.deque([0] * plotLength, maxlen=plotLength)
        self.x_buffer = collections.deque(
            [0] * plotLength, maxlen=plotLength)
        self.cur_count = 0
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

    def getSerialData(self, frame, ax):
        currentTimer = time.perf_counter()
        # the first reading will be erroneous
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)
        self.previousTimer = currentTimer

        # updating data
        value = self.rawData
        self.data.append(value)
        self.x_buffer.append(self.cur_count)

        self.cur_count += 1
        # plotting new plot
        plt.cla()
        plt.plot(self.x_buffer, self.data, label=['Channel 1'])
        # adding labels, title and text
        plt.title('STM Analog Read')
        plt.xlabel("time")
        plt.ylabel("AnalogRead Value")
        timeText = plt.text(0.50, 0.95, '', transform=ax.transAxes)
        lineValueText = plt.text(0.50, 0.90, '', transform=ax.transAxes)
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
        lineLabel = 'Potentiometer Value'
        lineValueText.set_text('[' + lineLabel + '] = ' + str(value))
        # self.csvData.append(self.data[-1])

    def backgroundThread(self):    # retrieve data
        time.sleep(1.0)  # give some buffer time for retrieving data
        self.serialConnection.reset_input_buffer()
        while (self.isRun):
            line = self.serialConnection.readline().decode('utf-8')[:-2]
            data = line.split(',')
            self.rawData = float(data[0])
            self.isReceiving = True

    def close(self):
        self.isRun = False
        self.thread.join()
        self.serialConnection.close()
        print('Disconnected...')
        # df = pd.DataFrame(self.csvData)
        # df.to_csv('data.csv')


def main():
    portName = 'COM10'
    baudRate = 115200
    maxPlotLength = 100
    dataNumBytes = 4        # number of bytes of 1 data point
    # initializes all required variables
    s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes)
    # starts background thread
    s.readSerialStart()

    # plotting starts below
    pltInterval = 50    # Period at which the plot animation updates [ms]
    ax = plt.axes()
    anim = animation.FuncAnimation(plt.gcf(), s.getSerialData, fargs=(
        ax,), interval=pltInterval)    # fargs has to be a tuple
    plt.legend(loc="upper left")

    plt.show()
    s.close()


if __name__ == '__main__':
    main()
