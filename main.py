#main file for ms3 rover simulation
import serial
import argparse
import binascii

class SimCourse:
    """class containing simulation courses"""
    sensor_array = []
    expected_command_array = []
    current_place = 0
    total_commands = 0

    def __init__(self, filename):
        #file object for course data
        with open(filename) as course_file:
            for num, line in enumerate(course_file, 1):
                if line[0] != '#' and line[0] != ' ':
                    as_bytes = bytearray.fromhex(line.partition('#')[0].rstrip())
                    if as_bytes.__len__() == 3:
                        self.total_commands += 1
                        as_bytes.insert(0, 0x01)
                        checksum = (as_bytes[1]+as_bytes[2]+as_bytes[3]) & 0x17
                        as_bytes.insert(4, checksum)
                        as_bytes.insert(5, 0x00)
                        self.sensor_array.append(as_bytes)
                        print("Read in sensor data:  ", binascii.hexlify(as_bytes))
                    elif as_bytes.__len__() == 5:
                        checksum = (as_bytes[1]+as_bytes[2]+as_bytes[3]+as_bytes[4]) & 0x17
                        as_bytes.append(0x00)
                        self.expected_command_array.append(as_bytes)
                        print("Read in expected move:", binascii.hexlify(as_bytes))

    def get_sensors(self):
        """returns perfect sensor values"""
        self.current_place += 1
        return self.sensor_array[self.current_place-1]

    def check_move_comm(self, move_comm):
        """checks for the expected movement command"""
        if self.expected_command_array[self.current_place-1] == move_comm:
            return True
        else:
            print("Incorrect move!\nExpected:", binascii.hexlify(self.expected_command_array[self.current_place-1]), "Got:", binascii.hexlify(move_comm))
            return False

    def get_movement(self):
        """returns perfect movement data"""
        distance_expected = [0x00, 0x00]
        if self.expected_command_array[self.current_place-1][0] == 0xBC:
            distance_expected[0] = 0x3C  # left
            distance_expected[1] = 0x3C  # right
        else:
            distance_expected[0] = self.expected_command_array[self.current_place-1][3]
            distance_expected[1] = self.expected_command_array[self.current_place-1][4]
        checksum = distance_expected[0] + distance_expected[1] & 0x17
        return bytes([0x04, 0x01, distance_expected[0], distance_expected[1], checksum, 0x00])

#time to parse command line args
parser = argparse.ArgumentParser(description='Simulate G3\'s rover over UART')
parser.add_argument("port", help="port to open UART connection on")
parser.add_argument("course_file", help="file to read course from")
args = parser.parse_args()

#object that will contain course data
course = SimCourse(args.course_file)

ser = serial.Serial(args.port, 19200, timeout=1)
if ser.isOpen():
    print("Opened port", args.port)

print("\n****SIMULATION BEGIN****")

#loop forever
while 1:
    msg = ser.read(6)
    if msg.__len__() == 6:
        if msg[0] == 0xAA:  # this is a req for sensor data
            print("Received:", "Sensor data request", binascii.hexlify(msg))
            reply = course.get_sensors()
            ser.write(reply)
            print("Replied: ", "Sensor data frame  ", binascii.hexlify(reply))
        elif msg[0] == 0xBA or msg[0] == 0xBC:  # this is a movement command
            print("Received:", "Movement command   ", binascii.hexlify(msg))
            if course.check_move_comm(msg):
                reply = bytearray([0x03, 0x00, 0x00, 0x00, 0x00, 0x00])
                ser.write(reply)
                print("Replied: ", "Movement comm ack  ", binascii.hexlify(reply))
            else:
                break
        elif msg[0] == 0xBB:  # this is a request for movement data
            reply = course.get_movement()
            ser.write(reply)
            if course.current_place == course.total_commands:
                print("End of simulation!")
                exit(0)
print("Simulation has exited upon failure.")
exit(-1)