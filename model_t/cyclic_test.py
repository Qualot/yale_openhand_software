import os
import time
import sys
from modelt import ModelT
from absl import app, flags

FLAGS = flags.FLAGS

flags.DEFINE_string('port', 'COM5', 'Port name of the Dynamixel device')
flags.DEFINE_integer('baudrate', 1000000, 'Baudrate of the Dynamixel device')
flags.DEFINE_integer('dxl_id', 1, 'Dynamixel ID of the gripper')
flags.DEFINE_integer('current_limit', 400, 'Current limit of the gripper')

if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def initiate_gripper(port, baudrate, dxl_id, current_limit):
    gripper = ModelT()
    gripper.device_name = port
    gripper.baudrate = baudrate
    gripper.dxl_id = dxl_id
    gripper.default_current_limit = current_limit
    print(f"Using port: {port}")
    print(f"Using baud rate: {baudrate}")
    print(f"Using dxl id: {dxl_id}")
    print(f"Using current limit: {current_limit}")
    if not gripper.connect():
        exit(0)
    if gripper.check_hw_error()[1]:
        gripper.reboot()
        time.sleep(1)
    gripper.set_defaults()
    return gripper

def cyclic_close_open(gripper: ModelT, current: int, loops: int, close_interval_sec: int, open_interval_sec: int):
    for i in range(loops):
        print(f"Cycle {i+1}/{loops}: Closing gripper with current goal {current}")
        gripper.close_gripper(current_goal=current)
        time.sleep(close_interval_sec)
        print(f"Cycle {i+1}/{loops}: Opening gripper")
        gripper.open_gripper()
        time.sleep(open_interval_sec)

def run(gripper: ModelT, upper_current_limit):
    current = 300
    current_limit = (0, upper_current_limit)
    while True:
        print("========================================")
        print(f"Current gripping current: {current}. Press 'q' to increase and 'a' to reduce. \nclose gripper: 'l' | open gripper: 'o' | reboot: 'r' | start cyclic: 'c' | quit: 'ESC'\nAny other key to latch closed state for 5 seconds!")
        keyboard = getch()
        print(keyboard)
        if keyboard == chr(0x1b):
            exit(0)
        if keyboard == 'o':
            gripper.open_gripper()
            continue
        if keyboard == 'l':
            gripper.close_gripper(current_goal=current)
            continue
        if keyboard == 'r':
            gripper.reboot()
            continue
        if keyboard == 'c':
            loops = int(input("Enter number of loops: "))
            close_interval_sec = float(input("Enter close interval seconds: "))
            open_interval_sec = float(input("Enter open interval seconds: "))
            cyclic_close_open(gripper, current, loops, close_interval_sec, open_interval_sec)
            continue
        if keyboard == 'q':
            current = min(current+10, current_limit[1])
            continue
        if keyboard == 'a':
            current = max(current-10, current_limit[0])
            continue
        gripper.latch_gripping(seconds=5, current_goal=current)

def main(argv):
    del argv  # Unused.
    
    port = FLAGS.port
    baudrate = FLAGS.baudrate
    dxl_id = FLAGS.dxl_id
    current_limit = FLAGS.current_limit

    gripper = initiate_gripper(port, baudrate, dxl_id, current_limit)
    run(gripper, current_limit)

if __name__ == "__main__":
    app.run(main)
