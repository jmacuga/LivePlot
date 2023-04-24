from threading import Thread
import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd

NUMBER_OF_SENSORS = 3


class serialPlot:

    def __init__(self,
                 serialPort='/dev/ttyACM0',
                 serialBaud=115200,
                 plotLength=100,
                 dataNumBytes=NUMBER_OF_SENSORS):
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.rawData = []
        self.data_buffers = [collections.deque(
            [0] * plotLength, maxlen=plotLength)
            for _ in range(NUMBER_OF_SENSORS)]
        self.mass_buffers = [collections.deque(
            [0] * plotLength, maxlen=plotLength)
            for _ in range(NUMBER_OF_SENSORS)]
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
            while self.isReceiving is not True:
                time.sleep(0.1)

    def plot_serial_data(self,
                         frame,
                         lines,
                         lineValueTexts,
                         lineLabels,
                         timeText):
        currentTimer = time.perf_counter()
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)
        self.previousTimer = currentTimer
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')

        for count, [buffer, line, lineValueText] in enumerate(
                zip(self.data_buffers, lines, lineValueTexts)):
            buffer.append(self.rawData[count])
            line.set_data(range(self.plotMaxLength), self.data_buffers[count])
            lineValueText.set_text(
                '[' + lineLabels[count] + '] = ' + str(self.rawData[count]))
        # self.csvData.append(self.data1[-1])

    def plot_mass(self,
                  frame,
                  lines,
                  lineValueTexts,
                  lineLabels,
                  timeText):
        currentTimer = time.perf_counter()
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)
        self.previousTimer = currentTimer
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')

        for count, [buffer, mass_buffer, line, lineValueText] in enumerate(
            zip(self.data_buffers,
                self.mass_buffers,
                lines,
                lineValueTexts)):
            mass = self.get_mass_power2(self.rawData[count])
            mass_buffer.append(mass)

            line.set_data(range(self.plotMaxLength), self.mass_buffers[count])
            lineValueText.set_text(
                '[' + lineLabels[count] + '] = ' + str(mass))
        # self.csvData.append(self.data1[-1])

    def backgroundThread(self):    # retrieve data
        time.sleep(1.0)  # give some buffer time for retrieving data
        self.serialConnection.reset_input_buffer()
        while (self.isRun):
            line = self.serialConnection.readline().decode('utf-8')[:-1]
            line.strip()
            data = line.split(',')
            try:
                self.rawData = [float(data[i])
                                for i in range(NUMBER_OF_SENSORS)]
            except TypeError:
                self.rawData = [0.0 for _ in range(NUMBER_OF_SENSORS)]
            except ValueError:
                self.rawData = [0.0 for _ in range(NUMBER_OF_SENSORS)]
            self.isReceiving = True
            # print(self.rawData)

    def close(self):
        self.isRun = False
        self.thread.join()
        self.serialConnection.close()
        print('Disconnected...')
        df = pd.DataFrame(self.csvData)
        df.to_csv('measured_data.csv')

    def get_mass_power2(self, voltage):
        # regression equation: f(X) = a*x^b+c
        if voltage == 0.0:
            return 0.0
        a = -0.856600000000000
        b = -0.893800000000000
        c = 3.135400000000000
        mass = pow((voltage - c) / a, 1/b)
        return mass


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
    ymax = 3.3
    fig = plt.figure()
    ax = plt.axes(xlim=(xmin, xmax), ylim=(
        float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
    ax.set_title('STM32 Analog Read')
    ax.set_xlabel("time")
    ax.set_ylabel("AnalogRead Value")

    labels = [f'Channel {sen_num + 1}' for sen_num in range(NUMBER_OF_SENSORS)]
    timeText = ax.text(0.50, 0.95, '', transform=ax.transAxes)
    lines = [ax.plot([], [], label=labels[sen_num])[0]
             for sen_num in range(NUMBER_OF_SENSORS)]
    offset = 0.05
    lineValueTexts = [ax.text(0.50, 0.90 - offset * sen_num,
                              '',
                              transform=ax.transAxes)
                      for sen_num in range(NUMBER_OF_SENSORS)]

    # _ = animation.FuncAnimation(fig, s.plot_serial_data, fargs=(
    #     lines, lineValueTexts, labels, timeText), interval=pltInterval)

    mass_animation = animation.FuncAnimation(fig, s.plot_mass, fargs=(
        lines, lineValueTexts, labels, timeText), interval=pltInterval)
    plt.legend(loc="upper left")
    plt.show()
    s.close()


if __name__ == '__main__':
    main()
