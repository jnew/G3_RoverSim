#main file for ms3 rover simulation
import serial


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
                as_bytes = bytearray.fromhex(line.partition('#')[0].rstrip())
                if (num % 2) != 0:
                    self.total_commands += 1
                    as_bytes.insert(0, 0x01)
                    checksum = (as_bytes[1]+as_bytes[2]+as_bytes[3]) & 0x17
                    as_bytes.insert(4, checksum)
                    self.sensor_array.append(as_bytes)
                    print("Read in sensor data:", as_bytes)
                else:
                    as_bytes.insert(0, 0xba)
                    checksum = (as_bytes[1]+as_bytes[2]) & 0x17
                    as_bytes.append(checksum)
                    as_bytes.append(0x00)
                    self.expected_command_array.append(as_bytes)
                    print("Read in expected move:", as_bytes)

    def get_sensors(self):
        """returns perfect sensor values"""
        self.current_place += 1
        return self.sensor_array[self.current_place-1]

    def check_move_comm(self, move_comm):
        """checks for the expected movement command"""
        if self.expected_command_array[self.current_place-1] == move_comm:
            return True
        else:
            print("Incorrect move!\nExpected:", self.expected_command_array[self.current_place-1], "Got:", move_comm)
            return False

    def get_movement(self, dist_msg):
        """returns perfect movement data"""
        distance_expected = dist_msg[2]
        checksum = distance_expected & 0x17
        return bytes([0x03, distance_expected, checksum, 0x00, 0x00])


ser = serial.Serial("COM22", 19200, timeout=1)
if ser.isOpen():
    print("Opened port")

#object that will contain course data
course = SimCourse('course_data.txt')

#loop forever
while 1:
    msg = ser.read(5)
    if msg.__len__() == 5:
        print("Received:", msg)
        if msg[0] == 0xAA:  # this is a req for sensor data
            reply = course.get_sensors()
            ser.write(reply)
            print("Replied: ", bytes(reply))
        elif msg[0] == 0xBA:  # this is a req for movement data
            if course.check_move_comm(msg):
                reply = course.get_movement(msg)
                ser.write(reply)
                print("Replied: ", bytes(reply))
            else:
                break
            if course.current_place == course.total_commands:
                print("End of simulation!")
                exit(0)
print("Simulation has exited upon failure.")
exit(-1)