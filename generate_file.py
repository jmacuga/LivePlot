import time
import serial
import csv


def save_to_csv(output_lines):
    with open("readings.csv", 'w') as csv_readings:
        csv_writer = csv.writer(csv_readings)
        readings = []
        for line in output_lines:
            reading_1, reading_2 = line.split(',')
            readings.append([reading_1, reading_2])
        csv_writer.writerows(readings)  


def save_serial_data(port, baudrate, timeout, samples):
    with serial.Serial() as ser:
        ser.port = port
        ser.baudrate = baudrate
        ser.timeout = timeout
        ser.open()
        time.sleep(1)
        output_lines = []
        while samples:
            samples -= 1
            while not ser.in_waiting:
                pass
            line = ser.readline()
            output_lines.append(line.decode('utf-8')[:-1])
        save_to_csv(output_lines)


if __name__ == '__main__':
    save_serial_data('/dev/ttyACM0', 115200, 1, 100)
