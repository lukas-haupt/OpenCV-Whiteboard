#!/usr/bin/env python3.9
""" AI Whiteboard

This program provides a user interface for capturing different hand gestures with a webcam.

The focus is on tracking hand movements, drawing and saving,
due to applicable hand gesture recognition, as well as other useful extensions.
"""

import copy
import math
import os
import tkinter
from tkinter import filedialog as fd
import screeninfo as si
import cv2 as cv
import mediapipe as mp
import numpy as np
import sys

__author__ = "Lukas Haupt, Stefan Weisbeck"
__credits__ = ["Lukas Haupt", "Stefan Weisbeck"]
__version__ = "1.1.0"
__maintainer__ = "Lukas Haupt"
__email__ = "luhaupt@uni-osnabrueck.de"
__status__ = "Development"

###################################################################################################
# GLOBALS                                                                                         #
###################################################################################################

# Whiteboard variables
whiteboard_width = 0
whiteboard_height = 0
NUMBER_OF_COLOR_CHANNELS = 3
window_name = "OpenCV-Whiteboard"

# Colors
WHITE = (255, 255, 255)
GRAY = (127, 127, 127)
DARK_GRAY = (63, 63, 63)
color_options = [
    ["Black", (0, 0, 0)],
    ["Blue", (255, 0, 0)],
    ["Green", (0, 255, 0)],
    ["Red", (0, 0, 255)]
]
color = None
color_key = 0
color_label = color_options[0][0]
AMOUNT_COLORS = len(color_options)

# Display
FONT = cv.FONT_HERSHEY_SIMPLEX
LINE_TYPE = cv.LINE_AA

# Calculations
HAND_INDICES = 21
SELECT_TOLERANCE = 40
ERASE_TOLERANCE = 20
COLOR_TOLERANCE = 25

# Button execution
loaded = None
cleared = None

# Function called when clicking the appropriate button
execute = ""

# Image saving
SEPARATOR = "_"
FILE_FORMAT = ".jpg"

# Image variables
cam = None
cam_width = 640
cam_height = 480
SCALED_CAM = (240, 160)

w_screen = None
w_screen_cached = np.full((whiteboard_height, whiteboard_width, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)

exit_program = 0

# Manipulation
first_draw = True
draw_start = None
draw_end = None
first_save = True
first_color_change = True
latest_index_tip_position = []
first_append = True

# Scale factor for index fingertip position
scale = [0, 0]

# Mouse coordinates and interaction list
mouse = [0, 0]
layers = []

# Mediapipe variables for drawing hand tracking coordinates
mp_drawing = mp.solutions.drawing_utils
# mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands


#def gstreamer_pipeline(
    #capture_width=1280,
    #capture_height=720,
    #display_width=1280,
    #display_height=720,
    #framerate=60,
    #flip_method=0,
#):
    #return (
        #"nvarguscamerasrc ! "
        #"video/x-raw(memory:NVMM), "
        #"width=(int)%d, height=(int)%d, "
        #"format=(string)NV12, framerate=(fraction)%d/1 ! "
        #"nvvidconv flip-method=%d ! "
        #"video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        #"videoconvert ! "
        #"video/x-raw, format=(string)BGR ! appsink"
        #% (
            #capture_width,
            #capture_height,
            #framerate,
            #flip_method,
            #display_width,
            #display_height,
        #)
    #)


def get_screen_resolution():
    """
    Get the resolution and offset of the primary monitor,
    as well as the scaling factor for the index fingertip point
    """
    global whiteboard_width
    global whiteboard_height
    global scale

    for m in si.get_monitors():
        if m.is_primary:
            whiteboard_width = m.width
            whiteboard_height = m.height

    scale[0] = whiteboard_width / cam_width
    scale[1] = whiteboard_height / cam_height


def distance(coord1=None, coord2=None):
    """ Calculate the euclidean distance between two hand landmarks """
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)


def point_is_in_rectangle(coord=None, x=0, y=0, width=0, height=0):
    """ Calculates if a given point @ref coord is in a given rectangle shaped area """
    return (x <= coord[0] <= (x + width)) and (y <= coord[1] <= (y + height))


def setup_windows():
    """ Initialize global variables cam and w_screen for the capture device and the white screen """
    global cam
    global w_screen
    global window_name
    global cam_width
    global cam_height
    global layers

    # Setup main window
    cv.namedWindow(window_name, cv.WND_PROP_FULLSCREEN)
    cv.setWindowProperty(window_name, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
    cv.setMouseCallback(window_name, check_mouse_event)

    # Setup capture device and whiteboard screen
    w_screen = np.full((whiteboard_height, whiteboard_width, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)
    cam = cv.VideoCapture(1)
    cam.set(cv.CAP_PROP_FRAME_WIDTH, cam_width)
    cam.set(cv.CAP_PROP_FRAME_HEIGHT, cam_height)

    # Create buttons
    create_button("Save")
    create_button("Load")
    create_button("Clear")
    create_button("Exit")
    print(layers[-1][2])


def create_button(label="", size_x=80, size_y=30):
    """ Create button with label and size """
    global color_options
    global layers
    global first_append

    # Set initial colors
    btn = np.full((size_y, size_x, NUMBER_OF_COLOR_CHANNELS), color_options[0][1], np.uint8)
    btn[2:size_y - 2, 2:size_x - 2] = GRAY

    # Get boundary of text as well as x and y coordinates
    label_size = cv.getTextSize(label, FONT, 1, 2)[0]
    label_x = int((size_x - label_size[0]) / 2)
    label_y = int((size_y + label_size[1]) / 2)

    cv.putText(btn, label, (label_x, label_y), FONT, 1, WHITE, 1, LINE_TYPE)

    # Append buttons to layer array with additional x- and y-offset according to the main window
    if first_append:
        first_append = False
        layers.append([btn, 50, size_y, label])
    else:
        layers.append([btn, 50, layers[-1][2] + (size_y * 2) if layers else (size_y * 2), label])


def check_mouse_event(event=0, mouse_x=0, mouse_y=0, flags=None, userdata=None):
    global mouse
    global w_screen
    global window_name
    global layers
    global execute
    global cleared

    if event == cv.EVENT_MOUSEMOVE:
        mouse[0] = mouse_x
        mouse[1] = mouse_y
        for lay in layers:
            if point_is_in_rectangle(mouse, lay[1], lay[2] + SCALED_CAM[1], lay[0].shape[1], lay[0].shape[0]):
                # Change appearance for highlighted layer
                lay[0][2:lay[0].shape[0] - 2, 2:lay[0].shape[1] - 2] = DARK_GRAY
                execute = lay[3]
            else:
                lay[0][2:lay[0].shape[0] - 2, 2:lay[0].shape[1] - 2] = GRAY

            label_size = cv.getTextSize(lay[3], FONT, 1, 1)[0]
            label_x = int((lay[0].shape[1] - label_size[0]) / 2)
            label_y = int((lay[0].shape[0] + label_size[1]) / 2)

            cv.putText(lay[0], lay[3], (label_x, label_y), FONT, 1, WHITE, 1, LINE_TYPE)

    if event == cv.EVENT_LBUTTONDOWN:
        if execute == "Save":
            save_screen()
        if execute == "Load":
            load_image()
        if execute == "Clear":
            cleared = np.full((whiteboard_height, whiteboard_width, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)
        if execute == "Exit":
            release_variables()


def release_variables():
    """ Release allocated variables """
    global cam

    cam.release()
    cv.destroyAllWindows()


def show_window(capture=None, index_coord=None, gesture="", col=color_options[0][1]):
    """ Display image in a single window """
    global w_screen
    global w_screen_cached
    global exit_program
    global window_name
    global layers
    global loaded
    global cleared

    if loaded is not None:
        w_screen = copy.deepcopy(loaded)
        loaded = None

    if cleared is not None:
        w_screen = copy.deepcopy(cleared)
        cleared = None

    # Create a deep copy of the whiteboard screen
    w_screen_cached = copy.deepcopy(w_screen)

    # Modify capture frame
    capture = cv.cvtColor(capture, cv.COLOR_RGB2BGR)
    capture = cv.flip(capture, 1)
    capture = cv.putText(capture, "Gesture: " + gesture, (20, 460), FONT, 0.75, color_options[0][1], 2, LINE_TYPE)
    capture = cv.putText(capture, "Gesture: " + gesture, (20, 460), FONT, 0.75, color_options[2][1], 1, LINE_TYPE)
    capture = cv.putText(capture, "Color: " + col, (300, 460), FONT, 0.75, color_options[0][1], 2, LINE_TYPE)
    capture = cv.putText(capture, "Color: " + col, (300, 460), FONT, 0.75, color_options[2][1], 1, LINE_TYPE)
    capture = cv.resize(capture, SCALED_CAM, 0, 0, interpolation=cv.INTER_CUBIC)

    if index_coord is not None:
        w_screen = cv.circle(w_screen, center=index_coord, radius=3, color=color, thickness=1, lineType=LINE_TYPE)

    w_screen = cv.flip(w_screen, 1)

    # Lay camera and buttons above whiteboard screen
    cap_off_y = capture.shape[0]
    cap_off_x = capture.shape[1]
    w_screen[0:cap_off_y, 0:cap_off_x] = capture
    for lay in layers:
        w_screen[cap_off_y + lay[2]:cap_off_y + lay[2] + lay[0].shape[0], lay[1]:lay[1] + lay[0].shape[1]] = lay[0]

    cv.imshow(window_name, w_screen)

    # Check if window has been closed by "q" or by default window close
    if cv.waitKey(1) == ord("q"):
        exit_program = 1


def check_user_gesture(landmarks=None):
    """ Check the image for a hand gesture and distinguish between them """
    draw_flag = False
    select_flag = False
    erase_flag = False
    color_flag = False

    # Split x and y coordinates into two separate arrays
    lm = np.array(landmarks)
    lmx_n, lmy_n = zip(*lm)

    lmx = []
    lmy = []

    # Calculate angle
    ang = math.acos(abs(lmy_n[5]-lmy_n[0])/abs(math.sqrt((lmy_n[5]-lmy_n[0])**2+(lmx_n[5]-lmx_n[0])**2)))

    # Rotation over 90°
    if lmy_n[0] < lmy_n[5]:
        ang = math.pi/2 + (math.pi/2-ang)

    # Rotation anticlockwise
    if lmx_n[0] < lmx_n[5]:
        ang *= -1

    # Offset for left or right hand

    # Up
    if abs(ang) <= .25 * math.pi:
        if lmx_n[5] > lmx_n[17]:
            ang += .5
        else:
            ang -= .5

    # Right
    elif .25 * math.pi < ang < .75 * math.pi:
        if lmy_n[5] < lmy_n[17]:
            ang += .5
        else:
            ang -= .5

    # Down
    elif abs(ang) >= .75 * math.pi:
        if lmx_n[5] < lmx_n[17]:
            ang += .5
        else:
            ang -= .5

    # Left
    elif -.25 * math.pi > ang > -.75 * math.pi:
        if lmy_n[5] > lmy_n[17]:
            ang += .5
        else:
            ang -= .5

    # Rotation
    for i in range(len(lmx_n)):
        x = lmx_n[i]
        y = lmy_n[i]
        lmx.append(math.cos(ang)*x - math.sin(ang)*y)
        lmy.append(math.sin(ang)*x + math.cos(ang)*y)

    # Gesture: DRAW
    for e in lmy[:6] + lmy[9:]:
        if e > lmy[6]:
            draw_flag = True
        else:
            draw_flag = False
            break

    # Gesture: SELECT
    if draw_flag:
        if distance(lm[4], lm[6]) > SELECT_TOLERANCE:
            draw_flag = False
            select_flag = True

    # Gesture: ERASE
    if distance(lm[4], lm[8]) < ERASE_TOLERANCE:
        erase_flag = True

    # Gesture SELECT COLOR
    for e in lmy[:12] + lmy[13:]:
        if e > lmy[12] and distance(lm[8], lm[12]) < COLOR_TOLERANCE and lmy[1] < lmy[0]:
            color_flag = True
        else:
            color_flag = False
            break

    if draw_flag:
        return "draw"
    if select_flag:
        return "select"
    if erase_flag:
        return "erase"
    if color_flag:
        # Gesture: SWITCH COLOR
        if lmx[4] < lmx[6]:
            return "switch color"
        return "select color"
    return "unknown"


def reverse_custom_layers():
    """ Reset the screen to the latest change before adding custom layers """
    global w_screen
    global w_screen_cached
    w_screen = copy.deepcopy(w_screen_cached)


def draw(coord=None, col=color, thickness=2):
    """ Function that is reliable for drawing the users input

    first_draw: flag is set to True, if the draw function has been called the first time
    draw_start: starting point of the line
    draw_end:   end point of the line
    """
    global w_screen
    global first_draw
    global draw_start
    global draw_end

    if first_draw:
        first_draw = False
        draw_start = coord
        draw_end = None
    else:
        draw_end = coord
        w_screen = cv.line(w_screen, draw_start, draw_end, col, thickness=thickness, lineType=LINE_TYPE)
        draw_start = draw_end


def switch_color():
    global color_options
    global color
    global color_key
    global color_label
    global first_color_change

    if first_color_change:
        first_color_change = False
        if color_key + 1 < AMOUNT_COLORS:
            color_key += 1
        else:
            color_key = 0

    color = color_options[color_key][1]
    color_label = color_options[color_key][0]


def save_screen():
    global w_screen_cached
    global execute

    execute = ""

    # Create the sub folder, if it does not exist
    sub_folder = "/Saves"
    path = os.getcwd() + sub_folder
    try:
        access_mode = 0o755
        os.mkdir(path=path, mode=access_mode)
    except FileExistsError:
        pass

    tkinter.Tk().withdraw()
    filename = fd.asksaveasfilename(defaultextension="", initialdir=path, filetypes=[("Images", ".jpg")])

    if filename:
        cv.imwrite(filename, cv.flip(w_screen_cached, 1))


def backup_screen():
    global w_screen_cached

    # Create the sub folder, if it does not exist
    path = os.getcwd() + "/Saves/"
    try:
        access_mode = 0o755
        os.mkdir(path=path, mode=access_mode)
    except FileExistsError:
        pass

    cv.imwrite(path + "BACKUP.png", cv.flip(w_screen_cached, 1))


def load_image():
    """ Load an image from the "Saves" subdirectory """
    global whiteboard_width
    global whiteboard_height
    global execute
    global loaded

    loaded_height = 0
    loaded_width = 0
    execute = ""

    # Create the sub folder, if it does not exist
    sub_folder = "/Saves"
    path = os.getcwd() + sub_folder
    try:
        access_mode = 0o755
        os.mkdir(path=path, mode=access_mode)
    except FileExistsError:
        pass

    tkinter.Tk().withdraw()
    filename = fd.askopenfilename(initialdir=path)
    try:
        loaded = cv.flip(cv.imread(filename), 1)
    except TypeError:
        pass

    # Check if loaded image has the same resolution as whiteboard, if not resize the loaded image
    if loaded is not None:
        loaded_height, loaded_width, _ = loaded.shape
        if loaded_height != whiteboard_height or loaded_width != whiteboard_width:
            loaded = cv.resize(loaded, (whiteboard_width, whiteboard_height), interpolation=cv.INTER_AREA)


def clear_screen():
    """ Get a new blank whiteboard screen """
    global w_screen
    w_screen = np.full((whiteboard_height, whiteboard_width, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)


def run():
    """ LOOP FUNCTION

    Calculate the 21 hand coordinates for tracking.
    Also manage settings for different user webcam input.
    """
    global cam
    global mp_drawing
    global mp_drawing_styles
    global mp_hands
    global first_draw
    global first_save
    global color
    global color_label
    global first_color_change
    global scale
    global execute

    execute = ""

    with mp_hands.Hands(
            max_num_hands=1,
            # model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
    ) as hands:
        while cam.isOpened() and not exit_program:
            success, frame = cam.read()
            if not success:
                print("Could not read correctly from open cameras!")
                backup_screen()
                print("Backup for whiteboard has been made!")
                break

            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            results = hands.process(frame)
            gesture = "unknown"
            scaled_index_tip = None

            if results.multi_hand_landmarks:
                # Array for gesture prediction
                landmarks = []
                for hand_landmarks in results.multi_hand_landmarks:
                    for lm in hand_landmarks.landmark:
                        # Adjust hand gesture coordinates to absolute frame values
                        lmx = int(lm.x * cam_width)
                        lmy = int(lm.y * cam_height)
                        landmarks.append([lmx, lmy])

                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
#                         mp_drawing_styles.get_default_hand_landmarks_style(),
#                         mp_drawing_styles.get_default_hand_connections_style()
                    )

                index_tip = landmarks[8]

                # Scale index fingertip position according to the scaling factor
                scaled_index_tip = [round(a * b) for a, b in zip(index_tip, scale)]

                gesture = check_user_gesture(landmarks)

                if gesture == "switch color":
                    switch_color()
                else:
                    first_color_change = True

                if gesture == "draw":
                    draw(scaled_index_tip, color, 2)
                elif gesture == "erase":
                    draw(scaled_index_tip, WHITE, 20)
                else:
                    first_draw = True

            show_window(frame, scaled_index_tip, gesture, color_label)
            reverse_custom_layers()


###################################################################################################
# MAIN FUNCTION                                                                                   #
###################################################################################################
def main():
    get_screen_resolution()
    setup_windows()
    run()
    release_variables()


if __name__ == "__main__":
    main()
