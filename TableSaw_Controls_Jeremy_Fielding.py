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

GPIO.setwarnings(False)

# setup pins
# Fence position outputs
DIR_f = 000  # Direction GPIO Pin for Fence
STEP_f = 000  # Step GPIO Pin
MAX_f = 99  # this is the dimension that should be displayed when the fence is on the max limit sensor
MIN_f = 0  # this is the dimension that should be displayed when the fence is on the min limit sensor
CW_f = 0  # Clockwise Rotation
CCW_f = 1  # Counterclockwise Rotation
# blade Angle outputs
DIR_a = 000  # Direction GPIO Pin
STEP_a = 0000  # Step GPIO Pin
MAX_a = 99
MIN_a = 0
CW_a = 0  # Clockwise Rotation
CCW_a = 1  # Counterclockwise Rotation
# blade height outputs
DIR_h = 000  # Direction GPIO Pin
STEP_h = 000  # Step GPIO Pin
MAX_h = 99
MIN_h = 0
CW_h = 0  # Clockwise Rotation
CCW_h = 1  # Counterclockwise Rotation

# Sensor inputs
fence_zero = 00  # GPIO Pin
fence_end = 00  # fence end of travel right side of blade
# fence_end_negative_position = 000  # fence end of travel negative if setup for other side of blade
blade_height_zero = 0
blade_height_end = 99
blade_angle_0 = 0
blade_angle_45 = 99
# emergency_stop = 22    # emergency_stop input stops all movement

# defining speed for motors
# Fence
RPM_f = 500
steps_per_revolution_f = 400
fdelay = 1 / ((RPM_f * steps_per_revolution_f) / 60)
stp_per_inch_f = 129.912814
# blade angle
RPM_a = 400
steps_per_revolution_a = 400
adelay = 1 / ((RPM_a * steps_per_revolution_a) / 60)
stp_per_inch_a = 147.853
# blade height
RPM_h = 900
steps_per_revolution_h = 400
hdelay = 1 / ((RPM_h * steps_per_revolution_h) / 60)
stp_per_inch_h = 6080

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

def move_fence():
    # setup variables
    global Current_fence_position
    Startposition = Current_fence_position.get()
    new_position = float(fen.get())

    # task to complete first
    fen.delete(0, END)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(DIR_f, GPIO.OUT)
    GPIO.setup(STEP_f, GPIO.OUT)
    GPIO.setup(fence_zero, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(fence_end, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # GPIO.setup(emergency_stop, GPIO.IN)

    if float(Startposition) < float(new_position):
        dis_to_move = float(new_position) - float(Startposition)

        move_fence_steps = int(stp_per_inch_f * float(dis_to_move))

        for steps in range(move_fence_steps):
            if GPIO.input(fence_end) == True:
                Current_fence_position.delete(0, END)
                Current_fence_position.insert(0, str(MAX_f))
                break
            GPIO.output(DIR_f, CW_f)
            GPIO.output(STEP_f, GPIO.HIGH)
            sleep(fdelay)
            GPIO.output(STEP_f, GPIO.LOW)
            sleep(fdelay)
            Current_fence_position.delete(0, END)
            Current_fence_position.insert(0, str(new_position))

    elif float(Startposition) > float(new_position):
        dis_to_move = float(Startposition) - float(new_position)

        move_fence_steps = int(stp_per_inch_f * float(dis_to_move))
        for steps in range(move_fence_steps):
            if GPIO.input(fence_zero) == True:
                Current_fence_position.delete(0, END)
                Current_fence_position.insert(0, str(MIN_f))
                break
            GPIO.output(DIR_f, CCW_f)
            GPIO.output(STEP_f, GPIO.HIGH)
            sleep(fdelay)
            GPIO.output(STEP_f, GPIO.LOW)
            sleep(fdelay)
            Current_fence_position.delete(0, END)
            Current_fence_position.insert(0, str(new_position))
    elif Startposition == new_position:
        return

    # reset things for next function
    GPIO.cleanup()


def change_angle():
    # setup variables
    global ang
    Startposition = C_angle_e.get()
    new_position = float(ang.get())

    # task to complete first
    ang.delete(0, END)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(DIR_a, GPIO.OUT)
    GPIO.setup(STEP_a, GPIO.OUT)
    GPIO.setup(blade_angle_0, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(blade_angle_45, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    if float(Startposition) < float(new_position):
        dis_to_move = float(new_position) - float(Startposition)

        move_angle_steps = int(stp_per_inch_a * float(dis_to_move))

        for steps in range(move_angle_steps):
            if GPIO.input(blade_angle_45) == True:
                C_angle_e.delete(0, END)
                C_angle_e.insert(0, str(MIN_a))
                break
            GPIO.output(DIR_a, CW_a)
            GPIO.output(STEP_a, GPIO.HIGH)
            sleep(adelay)
            GPIO.output(STEP_a, GPIO.LOW)
            sleep(adelay)
            C_angle_e.delete(0, END)
            C_angle_e.insert(0, str(new_position))

    elif float(Startposition) > float(new_position):
        dis_to_move = float(Startposition) - float(new_position)

        move_angle_steps = int(stp_per_inch_a * float(dis_to_move))
        for steps in range(move_angle_steps):
            if GPIO.input(blade_angle_0) == True:
                C_angle_e.delete(0, END)
                C_angle_e.insert(0, str(MAX_a))
                break
            GPIO.output(DIR_a, CCW_a)
            GPIO.output(STEP_a, GPIO.HIGH)
            sleep(adelay)
            GPIO.output(STEP_a, GPIO.LOW)
            sleep(adelay)
            C_angle_e.delete(0, END)
            C_angle_e.insert(0, str(new_position))

    elif Startposition == new_position:
        return

    # reset things for next function
    GPIO.cleanup()
    # C_angle_e.delete(0,END)
    # C_angle_e.insert(0, str(new_position))


def move_blade():
    # setup variables
    global C_height_e
    Startposition = C_height_e.get()
    new_position = float(height.get())

    # task to complete first
    height.delete(0, END)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(DIR_h, GPIO.OUT)
    GPIO.setup(STEP_h, GPIO.OUT)
    GPIO.setup(blade_height_zero, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(blade_height_end, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    if float(Startposition) < float(new_position):
        dis_to_move = float(new_position) - float(Startposition)

        move_height_steps = int(stp_per_inch_h * float(dis_to_move))

        for steps in range(move_height_steps):
            if GPIO.input(blade_height_end) == True:
                C_height_e.delete(0, END)
                C_height_e.insert(0, str(MAX_h))
                break
            GPIO.output(DIR_h, CW_h)
            GPIO.output(STEP_h, GPIO.HIGH)
            sleep(hdelay)
            GPIO.output(STEP_h, GPIO.LOW)
            sleep(hdelay)
            C_height_e.delete(0, END)
            C_height_e.insert(0, str(new_position))

    elif float(Startposition) > float(new_position):
        dis_to_move = float(Startposition) - float(new_position)

        move_height_steps = int(stp_per_inch_h * float(dis_to_move))
        for steps in range(move_height_steps):
            if GPIO.input(blade_height_zero) == True:
                C_height_e.delete(0, END)
                C_height_e.insert(0, str(MIN_h))
                break
            GPIO.output(DIR_h, CCW_h)
            GPIO.output(STEP_h, GPIO.HIGH)
            sleep(hdelay)
            GPIO.output(STEP_h, GPIO.LOW)
            sleep(hdelay)
            C_height_e.delete(0, END)
            C_height_e.insert(0, str(new_position))

    elif Startposition == new_position:
        return

    GPIO.cleanup()
    # C_height_e.delete(0,END)
    # C_height_e.insert(0, str(new_position))


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


def move_cal_to_height():
    C_num = float(cal.get())
    cal.delete(0, END)
    height.delete(0, END)
    height.insert(0, C_num)


def move_cal_to_fence_reset():
    C_num = float(cal.get())
    cal.delete(0, END)
    Current_fence_position.delete(0, END)
    Current_fence_position.insert(0, C_num)


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
button_decimal = Button(calculator_frame, text=".", padx=x_pad_button, pady=y_pad_button, command=lambda: button_click("."))
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
button_change_angle = Button(angle_frame, text="Change Angle", padx=x_pad_button, pady=y_pad_button, command=change_angle)
button_moveblade = Button(height_frame, text="Move blade", padx=x_pad_button, pady=y_pad_button, command=move_blade)

button_change_angle_45 = Button(angle_frame, text="Go To 45", padx=x_pad_button, pady=y_pad_button, command=shortcut_a45)
button_moveblade_0 = Button(height_frame, text="Go To 0", padx=x_pad_button, pady=y_pad_button, command=shortcut_h0)
button_change_angle_0 = Button(angle_frame, text="Go To 0", padx=x_pad_button, pady=y_pad_button, command=shortcut_a0)
button_moveblade_1 = Button(height_frame, text="Go To 1.0", padx=x_pad_button, pady=y_pad_button, command=shortcut_h1)

cal_to_fen_but = Button(fence_frame, text="Grab number", padx=x_pad_button, pady=y_pad_button, command=move_cal_to_fence)
cal_to_ang_but = Button(angle_frame, text="Grab number", padx=x_pad_button, pady=y_pad_button, command=move_cal_to_angle)
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

root.mainloop()
