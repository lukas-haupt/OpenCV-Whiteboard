#!/usr/bin/env python3.9
""" AI Whiteboard

This program provides a user interface for capturing different hand gestures with a webcam.

The focus is on tracking hand movements, drawing and saving,
due to applicable hand gesture recognition, as well as other useful extensions.
"""

import copy
import datetime as dt
import math
import os
import tkinter
from tkinter import filedialog as fd
import screeninfo as si
import cv2 as cv
import mediapipe as mp
import numpy as np

__author__ = "Lukas Haupt"
__credits__ = ["Lukas Haupt"]
__version__ = "1.0.0"
__maintainer__ = "Lukas Haupt"
__email__ = "luhaupt@uni-osnabrueck.de"
__status__ = "Production"

###################################################################################################
# GLOBALS                                                                                         #
###################################################################################################

# Whiteboard variables
whiteboard_width = 0
whiteboard_height = 0
whiteboard_offset_x = 0
whiteboard_offset_y = 0
NUMBER_OF_COLOR_CHANNELS = 3
window_name = "OpenCV-Whiteboard"

# Colors
WHITE = (255, 255, 255)
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

# Image saving
SEPARATOR = "_"
FILE_FORMAT = ".jpg"

# Image variables
cam = None
cam_width = 640
cam_height = 480
SCALED_CAM = (480, 360)

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

# Scale factor for index fingertip position
scale = [0, 0]

# Mediapipe variables for drawing hand tracking coordinates
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands


def get_screen_resolution():
    """
    Get the resolution and offset of the primary monitor,
    as well as the scaling factor for the index fingertip point
    """
    global whiteboard_width
    global whiteboard_height
    global whiteboard_offset_x
    global whiteboard_offset_y
    global scale

    for m in si.get_monitors():
        if m.is_primary:
            whiteboard_width = m.width
            whiteboard_height = m.height
            whiteboard_offset_x = m.x
            whiteboard_offset_y = m.y

    scale[0] = whiteboard_width / cam_width
    scale[1] = whiteboard_height / cam_height


def distance(coord1=None, coord2=None):
    """ Calculate the euclidean distance between two hand landmarks """
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)


def setup_windows():
    """ Initialize global variables cam and w_screen for the capture device and the white screen """
    global cam
    global w_screen
    global window_name
    global whiteboard_offset_x
    global whiteboard_offset_y
    global cam_width
    global cam_height

    cv.namedWindow(window_name, cv.WINDOW_GUI_NORMAL)
    cv.setWindowProperty(window_name, cv.WINDOW_FULLSCREEN, cv.WINDOW_FULLSCREEN)
    cv.moveWindow(window_name, whiteboard_offset_x, whiteboard_offset_y)

    w_screen = np.full((whiteboard_height, whiteboard_width, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)
    cam = cv.VideoCapture(-1)
    cam.set(cv.CAP_PROP_FRAME_WIDTH, cam_width)
    cam.set(cv.CAP_PROP_FRAME_HEIGHT, cam_height)


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

    # Lay camera above whiteboard screen
    w_screen[0:capture.shape[0], 0:capture.shape[1]] = capture

    cv.imshow(window_name, w_screen)

    # Check if window has been closed by "q" or by default window close
    if cv.waitKey(1) == ord("q") or cv.getWindowProperty(window_name, cv.WND_PROP_VISIBLE) < 1:
        exit_program = 1


def check_user_gesture(landmarks=None):
    """ Check the image for a hand gesture and distinguish between them """
    draw_flag = False
    select_flag = False
    erase_flag = False
    save_flag = False
    clear_flag = False
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

    # Offset
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

    # Gesture: SAVE
    for e in lmy[:2] + lmy[5:]:
        if e > lmy[2] and lmx[5] > lmx[2] and lmx[9] > lmx[2] and lmx[13] > lmx[2] and lmx[17] > lmx[2]:
            save_flag = True
        else:
            save_flag = False
            break

    # Gesture: CLEAR
    for e in lmy[:2] + lmy[5:]:
        if e < lmy[2] and lmx[5] > lmx[2] and lmx[9] > lmx[2] and lmx[13] > lmx[2] and lmx[17] > lmx[2]:
            clear_flag = True
        else:
            clear_flag = False
            break

    # Gesture: SAVE/CLEAR - Fingers must be closed for saving or clearing the screen
    if lmx[8] > lmx[5] or lmx[12] > lmx[9] or lmx[16] > lmx[13] or lmx[20] > lmx[17]:
        save_flag = False
        clear_flag = False

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
    if save_flag:
        return "save"
    if clear_flag:
        return "clear"
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
    global w_screen

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
        cv.imwrite(filename, cv.flip(w_screen, 1))


def quicksave_screen():
    """ Save the current whiteboard screen into a subdirectory """
    global w_screen
    global first_save

    # Create the sub folder, if it does not exist
    sub_folder = "/Saves"
    path = os.getcwd() + sub_folder
    try:
        access_mode = 0o755
        os.mkdir(path=path, mode=access_mode)
    except FileExistsError:
        pass

    # Get current date
    current_date = dt.datetime.now()
    date_str = SEPARATOR.join(("", str(current_date.year), str(current_date.month), str(current_date.day),
                               str(current_date.hour), str(current_date.minute), str(current_date.second)))

    if first_save:
        # Save w_screen
        filename = "savedImage" + date_str + FILE_FORMAT
        cv.imwrite(os.path.join(path, filename), cv.flip(w_screen, 1))
        first_save = False


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
    global w_screen
    global mp_drawing
    global mp_drawing_styles
    global mp_hands
    global first_draw
    global first_save
    global color
    global color_label
    global first_color_change
    global scale

    with mp_hands.Hands(
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
    ) as hands:
        while cam.isOpened() and not exit_program:
            success, frame = cam.read()
            if not success:
                print("Could not read correctly from open cameras!")
                continue

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
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style()
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

                if gesture == "save":
                    quicksave_screen()
                else:
                    first_save = True

                if gesture == "clear":
                    clear_screen()

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
