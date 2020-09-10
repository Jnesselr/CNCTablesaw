# Written By: Jeremy Fielding
# Project based on Youtube Video https://youtu.be/JEImn7s7x1o
from tkinter import *
from time import sleep
import RPi.GPIO as GPIO

root = Tk()
root.title("Table Saw Controls")

# change the size of buttons and frames
x_pad_frame = 0
x_pad_button = 10
x_pad_nums = 15
x_pad_symbols = 15
y_pad_button = 10

calculator_frame = LabelFrame(root, text="Calculator", padx=x_pad_frame, pady=20)
calculator_frame.grid(row=0, column=0, padx=5, pady=10)

fence_frame = LabelFrame(root, text="Fence", padx=x_pad_frame, pady=20)
fence_frame.grid(row=0, column=1, sticky=N, padx=5, pady=10)

angle_frame = LabelFrame(root, text="Angle", padx=x_pad_frame, pady=20)
angle_frame.grid(row=0, column=2, sticky=N, padx=5, pady=10)

height_frame = LabelFrame(root, text="Blade Height", padx=x_pad_frame, pady=20)
height_frame.grid(row=0, column=3, sticky=N, padx=5, pady=10)

# setup pins
# Fence position outputs
MAX_f = 99  # this is the dimension that should be displayed when the fence is on the max limit sensor
MIN_f = 0  # this is the dimension that should be displayed when the fence is on the min limit sensor
# blade Angle outputs
MAX_a = 99
MIN_a = 0
# blade height outputs
MAX_h = 99
MIN_h = 0


class EndstopHit(Exception):
    MAX = "max"
    MIN = "min"

    def __init__(self, endstop):
        self.endstop = endstop


class StepperMotor(object):
    def __init__(self,
                 direction_pin,
                 step_pin,
                 steps_per_inch,
                 rotations_per_minute,
                 steps_per_revolution=400,
                 minimum_input_pin=None,
                 maximum_input_pin=None,
                 invert=False):
        self._direction_pin = direction_pin
        self._step_pin = step_pin
        self._steps_per_inch = steps_per_inch
        self._rotations_per_minute = rotations_per_minute
        self._steps_per_revolution = steps_per_revolution
        self._minimum_input_pin = minimum_input_pin
        self._maximum_input_pin = maximum_input_pin
        self._current_position = 0
        self._clockwise_state = 0 if invert else 1
        self._counterclockwise_state = 1 if invert else 0

    @property
    def current_position(self):
        return self._current_position

    @current_position.setter
    def current_position(self, value):
        self._current_position = value

    def setup(self):
        GPIO.setup(self._direction_pin, GPIO.OUT)
        GPIO.setup(self._step_pin, GPIO.OUT)
        if self._minimum_input_pin is not None:
            GPIO.setup(self._minimum_input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        if self._maximum_input_pin is not None:
            GPIO.setup(self._maximum_input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def move_to(self, new_position):
        new_position = float(new_position)
        if self._current_position < new_position:
            GPIO.output(self._direction_pin, self._clockwise_state)
            endstop_to_check = self._maximum_input_pin
            endstop_exception = EndstopHit(EndstopHit.MAX)
        elif self._current_position > new_position:
            GPIO.output(self._direction_pin, self._counterclockwise_state)
            endstop_to_check = self._maximum_input_pin
            endstop_exception = EndstopHit(EndstopHit.MIN)
        else:
            return  # We're already where we need to be

        distance_to_move = abs(new_position - self._current_position)
        steps_to_move = int(self._steps_per_inch * float(distance_to_move))

        delay = 1 / ((self._rotations_per_minute * self._steps_per_revolution) / 60)

        for step in range(steps_to_move):
            if endstop_to_check is not None and GPIO.input(endstop_to_check):
                raise endstop_exception

            GPIO.output(self._step_pin, GPIO.HIGH)
            sleep(delay / 2)
            GPIO.output(self._step_pin, GPIO.LOW)
            sleep(delay / 2)


fence_stepper_motor = StepperMotor(
    direction_pin=000,
    step_pin=000,
    steps_per_inch=129.912814,
    rotations_per_minute=500,
    minimum_input_pin=00,
    maximum_input_pin=99
)

blade_angle_stepper_motor = StepperMotor(
    direction_pin=000,
    step_pin=000,
    steps_per_inch=147.853,
    rotations_per_minute=400,
    minimum_input_pin=00,
    maximum_input_pin=99
)

blade_height_stepper_motor = StepperMotor(
    direction_pin=000,
    step_pin=000,
    steps_per_inch=6080,
    rotations_per_minute=900,
    minimum_input_pin=00,
    maximum_input_pin=99
)

# Entry panels and locations
cal = Entry(calculator_frame, width=10, borderwidth=5)
cal.grid(row=0, column=0, columnspan=3, padx=0, pady=10)

fen = Entry(fence_frame, width=10, borderwidth=5)
fen.grid(row=0, column=0, columnspan=2, padx=0, pady=10)
fen.insert(0, 0)

ang = Entry(angle_frame, width=10, borderwidth=5)
ang.grid(row=0, column=0, columnspan=2, padx=0, pady=10)
ang.insert(0, 0)

height = Entry(height_frame, width=10, borderwidth=5)
height.grid(row=0, column=0, columnspan=2, padx=0, pady=10)
height.insert(0, 0)

C_fence_position = Label(fence_frame, text="Current Position = ", font=("Arial", 12))
C_fence_position.grid(row=3, column=0)

Current_fence_position = Entry(fence_frame, width=7, borderwidth=2)
Current_fence_position.grid(row=3, column=1)
Current_fence_position.insert(0, 0)

C_angle = Label(angle_frame, text="Current Angle = ", font=("Arial", 12))
C_angle.grid(row=3, column=0)

C_angle_e = Entry(angle_frame, width=7, borderwidth=2)
C_angle_e.grid(row=3, column=1)
C_angle_e.insert(0, 0)

C_blade_height = Label(height_frame, text="Current Height = ", font=("Arial", 12))
C_blade_height.grid(row=3, column=0)

C_height_e = Entry(height_frame, width=7, borderwidth=2, relief=SUNKEN)
C_height_e.grid(row=3, column=1)
C_height_e.insert(0, 0)


# Calculator functions

def button_click(number):
    current = cal.get()
    cal.delete(0, END)
    cal.insert(0, str(current) + str(number))


def button_clear():
    cal.delete(0, END)


def button_add():
    first_number = cal.get()
    global f_num
    global math
    math = "addition"
    f_num = float(first_number)
    cal.delete(0, END)


def button_equal():
    second_number = cal.get()
    cal.delete(0, END)

    if math == "addition":
        cal.insert(0, f_num + float(second_number))

    if math == "subtraction":
        cal.insert(0, f_num - float(second_number))

    if math == "multiplication":
        cal.insert(0, f_num * float(second_number))

    if math == "division":
        cal.insert(0, f_num / float(second_number))


def button_subtract():
    first_number = cal.get()
    global f_num
    global math
    math = "subtraction"
    f_num = float(first_number)
    cal.delete(0, END)


def button_multiply():
    first_number = cal.get()
    global f_num
    global math
    math = "multiplication"
    f_num = float(first_number)
    cal.delete(0, END)


def button_divide():
    first_number = cal.get()
    global f_num
    global math
    math = "division"
    f_num = float(first_number)
    cal.delete(0, END)


# Move motors
def move(stepper_motor, new_position_entry, current_position_entry, min_value, max_value):
    # setup variables
    new_position = float(new_position_entry.get())

    # task to complete first
    new_position_entry.delete(0, END)

    try:
        stepper_motor.move_to(new_position)
        current_position_entry.delete(0, END)
        current_position_entry.insert(0, str(new_position))
    except EndstopHit as e:
        if e.endstop == EndstopHit.MAX:
            current_position_entry.delete(0, END)
            current_position_entry.insert(0, str(max_value))
        elif e.endstop == EndstopHit.MIN:
            current_position_entry.delete(0, END)
            current_position_entry.insert(0, str(min_value))
        else:
            raise


def move_fence():
    move(fence_stepper_motor, fen, Current_fence_position, MIN_f, MAX_f)


def move_blade_angle():
    move(blade_angle_stepper_motor, ang, C_angle_e, MIN_a, MAX_a)


def move_blade_height():
    move(blade_height_stepper_motor, height, C_height_e, MIN_h, MAX_h)


def shortcut_a45():
    C_num = 45.0
    cal.delete(0, END)
    ang.delete(0, END)
    ang.insert(0, C_num)


def shortcut_a0():
    C_num = 0.0
    cal.delete(0, END)
    ang.delete(0, END)
    ang.insert(0, C_num)


def shortcut_h1():
    C_num = 1.0
    cal.delete(0, END)
    height.delete(0, END)
    height.insert(0, C_num)


def shortcut_h0():
    C_num = 0
    cal.delete(0, END)
    height.delete(0, END)
    height.insert(0, C_num)


def Inch_to_mm():
    C_num = cal.get()
    ans_in_mm = float(C_num) * 25.4
    cal.delete(0, END)
    cal.insert(0, ans_in_mm)


def mm_to_Inch():
    C_num = cal.get()
    ans_in_inch = float(C_num) / 25.4
    cal.delete(0, END)
    cal.insert(0, ans_in_inch)


def move_cal_to_fence():
    C_num = float(cal.get())
    cal.delete(0, END)
    fen.delete(0, END)
    fen.insert(0, C_num)


def move_cal_to_angle():
    C_num = float(cal.get())
    cal.delete(0, END)
    ang.delete(0, END)
    ang.insert(0, C_num)
    blade_angle_stepper_motor.current_position = C_num


def move_cal_to_height():
    C_num = float(cal.get())
    cal.delete(0, END)
    height.delete(0, END)
    height.insert(0, C_num)
    blade_height_stepper_motor.current_position = C_num


def move_cal_to_fence_reset():
    C_num = float(cal.get())
    cal.delete(0, END)
    Current_fence_position.delete(0, END)
    Current_fence_position.insert(0, C_num)
    fence_stepper_motor.current_position = C_num


def move_cal_to_angle_reset():
    C_num = float(cal.get())
    cal.delete(0, END)
    C_angle_e.delete(0, END)
    C_angle_e.insert(0, C_num)


def move_cal_to_height_reset():
    C_num = float(cal.get())
    cal.delete(0, END)
    C_height_e.delete(0, END)
    C_height_e.insert(0, C_num)


def clear_fen():
    fen.delete(0, END)


def clear_ang():
    ang.delete(0, END)


def clear_height():
    height.delete(0, END)


# Define Calculator Buttons

button_1 = Button(calculator_frame, text="1", padx=x_pad_nums, pady=y_pad_button, command=lambda: button_click(1))
button_2 = Button(calculator_frame, text="2", padx=x_pad_nums, pady=y_pad_button, command=lambda: button_click(2))
button_3 = Button(calculator_frame, text="3", padx=x_pad_nums, pady=y_pad_button, command=lambda: button_click(3))
button_4 = Button(calculator_frame, text="4", padx=x_pad_nums, pady=y_pad_button, command=lambda: button_click(4))
button_5 = Button(calculator_frame, text="5", padx=x_pad_nums, pady=y_pad_button, command=lambda: button_click(5))
button_6 = Button(calculator_frame, text="6", padx=x_pad_nums, pady=y_pad_button, command=lambda: button_click(6))
button_7 = Button(calculator_frame, text="7", padx=x_pad_nums, pady=y_pad_button, command=lambda: button_click(7))
button_8 = Button(calculator_frame, text="8", padx=x_pad_nums, pady=y_pad_button, command=lambda: button_click(8))
button_9 = Button(calculator_frame, text="9", padx=x_pad_nums, pady=y_pad_button, command=lambda: button_click(9))
button_0 = Button(calculator_frame, text="0", padx=x_pad_nums, pady=y_pad_button, command=lambda: button_click(0))
button_decimal = Button(calculator_frame, text=".", padx=x_pad_button, pady=y_pad_button,
                        command=lambda: button_click("."))
button_add = Button(calculator_frame, text="+", padx=x_pad_symbols, pady=y_pad_button, command=button_add)
button_equal = Button(calculator_frame, text="=", padx=30, pady=y_pad_button, command=button_equal)
button_clear = Button(calculator_frame, text="Clear", padx=20, pady=y_pad_button, command=button_clear)
button_subtract = Button(calculator_frame, text="-", padx=x_pad_symbols, pady=y_pad_button, command=button_subtract)
button_multiply = Button(calculator_frame, text="*", padx=x_pad_symbols, pady=y_pad_button, command=button_multiply)
button_divide = Button(calculator_frame, text="/", padx=x_pad_symbols, pady=y_pad_button, command=button_divide)

inch_to_mm = Button(calculator_frame, text="Inch to mm", padx=x_pad_button, pady=y_pad_button, command=Inch_to_mm)
mm_to_inch = Button(calculator_frame, text="mm to Inch", padx=x_pad_button, pady=y_pad_button, command=mm_to_Inch)

# Define Other Buttons

button_movefence = Button(fence_frame, text="Move Fence", padx=x_pad_button, pady=y_pad_button, command=move_fence)
button_change_angle = Button(angle_frame, text="Change Angle", padx=x_pad_button, pady=y_pad_button,
                             command=move_blade_angle)
button_moveblade = Button(height_frame, text="Move blade", padx=x_pad_button, pady=y_pad_button, command=move_blade_height)

button_change_angle_45 = Button(angle_frame, text="Go To 45", padx=x_pad_button, pady=y_pad_button,
                                command=shortcut_a45)
button_moveblade_0 = Button(height_frame, text="Go To 0", padx=x_pad_button, pady=y_pad_button, command=shortcut_h0)
button_change_angle_0 = Button(angle_frame, text="Go To 0", padx=x_pad_button, pady=y_pad_button, command=shortcut_a0)
button_moveblade_1 = Button(height_frame, text="Go To 1.0", padx=x_pad_button, pady=y_pad_button, command=shortcut_h1)

cal_to_fen_but = Button(fence_frame, text="Grab number", padx=x_pad_button, pady=y_pad_button,
                        command=move_cal_to_fence)
cal_to_ang_but = Button(angle_frame, text="Grab number", padx=x_pad_button, pady=y_pad_button,
                        command=move_cal_to_angle)
cal_to_height_but = Button(height_frame, text="Grab number", padx=x_pad_button, pady=y_pad_button,
                           command=move_cal_to_height)

cal_to_fen_but_reset = Button(fence_frame, text="Grab number", padx=x_pad_button, pady=y_pad_button,
                              command=move_cal_to_fence_reset)
cal_to_ang_but_reset = Button(angle_frame, text="Grab number", padx=x_pad_button, pady=y_pad_button,
                              command=move_cal_to_angle_reset)
cal_to_height_but_reset = Button(height_frame, text="Grab number", padx=x_pad_button, pady=y_pad_button,
                                 command=move_cal_to_height_reset)

clear_fen_but = Button(fence_frame, text="Clear", padx=x_pad_button, pady=y_pad_button, command=clear_fen)
clear_ang_but = Button(angle_frame, text="Clear", padx=x_pad_button, pady=y_pad_button, command=clear_ang)
clear_height_but = Button(height_frame, text="Clear", padx=x_pad_button, pady=y_pad_button, command=clear_height)

# Put the buttons on the screen

button_1.grid(row=3, column=0)
button_2.grid(row=3, column=1)
button_3.grid(row=3, column=2)

button_4.grid(row=2, column=0)
button_5.grid(row=2, column=1)
button_6.grid(row=2, column=2)

button_7.grid(row=1, column=0)
button_8.grid(row=1, column=1)
button_9.grid(row=1, column=2)

button_0.grid(row=4, column=0)
button_clear.grid(row=4, column=1, columnspan=2)
button_add.grid(row=5, column=0)
button_equal.grid(row=5, column=1, columnspan=2)

button_subtract.grid(row=6, column=0)
button_multiply.grid(row=6, column=1)
button_divide.grid(row=6, column=2)
button_decimal.grid(row=6, column=3)
inch_to_mm.grid(row=8, column=0, columnspan=3)
mm_to_inch.grid(row=7, column=0, columnspan=3)

button_movefence.grid(row=1, column=0)
button_change_angle.grid(row=1, column=0)
button_moveblade.grid(row=1, column=0)

button_change_angle_45.grid(row=5, column=0)
button_moveblade_0.grid(row=5, column=0)
button_change_angle_0.grid(row=5, column=1)
button_moveblade_1.grid(row=5, column=1)

cal_to_fen_but.grid(row=1, column=1)
cal_to_ang_but.grid(row=1, column=1)
cal_to_height_but.grid(row=1, column=1)

cal_to_fen_but_reset.grid(row=4, column=1)
cal_to_ang_but_reset.grid(row=4, column=1)
cal_to_height_but_reset.grid(row=4, column=1)

clear_fen_but.grid(row=2, column=0)
clear_ang_but.grid(row=2, column=0)
clear_height_but.grid(row=2, column=0)

try:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    fence_stepper_motor.setup()
    blade_angle_stepper_motor.setup()
    blade_height_stepper_motor.setup()

    root.mainloop()
finally:
    GPIO.cleanup()
