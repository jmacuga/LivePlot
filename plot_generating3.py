from threading import Thread
import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd

NUMBER_OF_SENSORS = 2

class serialPlot:

    def __init__(self, serialPort='/dev/ttyACM0', serialBaud=115200, plotLength=100, dataNumBytes=2):
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.rawData = ''
        self.data_buffers = [collections.deque([0] * plotLength, maxlen=plotLength) for channel_num in range(NUMBER_OF_SENSORS)]
        # self.data1 = collections.deque([0] * plotLength, maxlen=plotLength)
        # self.data2 = collections.deque([0] * plotLength, maxlen=plotLength)
        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.plotTimer = 0
        self.previousTimer = 0
        self.csvData = []

        print('Trying to connect to: ' + str(serialPort) +
              ' at ' + str(serialBaud) + ' BAUD.')
        try:
            self.serialConnection = serial.Serial(
                serialPort, serialBaud, timeout=4)
            print('Connected to ' + str(serialPort) +
                  ' at ' + str(serialBaud) + ' BAUD.')
        except Exception as e:
            print("Failed to connect with " + str(serialPort) +
                  ' at ' + str(serialBaud) + ' BAUD.')
            print(e)

    def readSerialStart(self):
        if self.thread is None:
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            # Block till we start receiving values
            while self.isReceiving != True:
                time.sleep(0.1)

    def getSerialData(self, frame, lines, lineValueTexts, lineLabels, timeText):
        currentTimer = time.perf_counter()
        # the first reading will be erroneous
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)
        self.previousTimer = currentTimer
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')      
        # we get the latest data point and append it to our array
        for count, buffer in enumerate(self.data_buffers):
            buffer.append(self.rawData[count])
        for count, line in enumerate(lines):
            line.set_data(range(self.plotMaxLength), self.data_buffers[count])

        for count, lineValueText in enumerate(lineValueTexts):
            lineValueText.set_text('[' + lineLabels[count] + '] = ' + str(self.rawData[count]))
            
        # self.csvData.append(self.data1[-1])

    def backgroundThread(self):    # retrieve data
        time.sleep(1.0)  # give some buffer time for retrieving data
        self.serialConnection.reset_input_buffer()
        while (self.isRun):
            line = self.serialConnection.readline().decode('utf-8')[:-1]
            line.strip()
            data = line.split(',')
            try:
                self.rawData = (float(data[0]), float(data[1]))
            except ValueError:
                return
            except TypeError:
                return
            self.isReceiving = True
            # print(self.rawData)

    def close(self):
        self.isRun = False
        self.thread.join()
        self.serialConnection.close()
        print('Disconnected...')
        df = pd.DataFrame(self.csvData)
        df.to_csv('measured_data.csv')


def main():

    # portName = 'COM5'     # for windows users
    portName = '/dev/ttyACM0'
    baudRate = 115200
    maxPlotLength = 100
    dataNumBytes = 4  
    # number of bytes of 1 data point
    # initializes all required variables
    s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes)
    # starts background thread
    s.readSerialStart()

    # plotting starts below
    pltInterval = 50    # Period at which the plot animation updates [ms]
    xmin = 0
    xmax = maxPlotLength
    ymin = -(1)
    ymax = 1
    fig = plt.figure()
    ax = plt.axes(xlim=(xmin, xmax), ylim=( 
        float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
    ax.set_title('STM32 Analog Read')
    ax.set_xlabel("time")
    ax.set_ylabel("AnalogRead Value")

    labels = [f'Channel {sen_num + 1}' for sen_num in range(NUMBER_OF_SENSORS)]
    timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
    lines = [ax.plot([], [], label=labels[sen_num])[0] for sen_num in range(NUMBER_OF_SENSORS)]
    offset = 0.05
    lineValueTexts = [ax.text(0.50, 0.90 - offset * sen_num, '', transform=ax.transAxes) for sen_num in range(NUMBER_OF_SENSORS) ]

    anim = animation.FuncAnimation(fig, s.getSerialData, fargs=(lines, lineValueTexts, labels, timeText), interval=pltInterval)    # fargs has to be a tuple
    plt.legend(loc="upper left")
    plt.show()
    s.close()


if __name__ == '__main__':
    main()
