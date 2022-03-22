#!/usr/bin/env python3.9

###################################################################################################
# HEADER                                                                                          #
###################################################################################################

""" OpenCV-Whiteboard

This program provides a user interface for capturing different hand gestures with a webcam.

The focus is on tracking hand movements, drawing and saving,
due to applicable hand gesture recognition, as well as other useful extensions.
"""

__author__ = "Lukas Haupt, Stefan Weisbeck"
__credits__ = ["Lukas Haupt", "Stefan Weisbeck"]
__version__ = "2.0.0"
__maintainer__ = "Lukas Haupt"
__email__ = "luhaupt@uni-osnabrueck.de"
__status__ = "Production"


###################################################################################################
# IMPORTS                                                                                         #
###################################################################################################

import copy                             # Deep copies
import math                             # Calculations
import os                               # Filesystem
import tkinter                          # GUI-Toolkit
from tkinter import filedialog as fd    # GUI for save/load functionality

import cv2 as cv                        # Image processing
import mediapipe as mp                  # Hand tracking
import numpy as np                      # Calculations
import screeninfo as si                 # Screen resolution


###################################################################################################
# GLOBALS                                                                                         #
###################################################################################################

# ----- WINDOW -----

# Whiteboard variables
whiteboard_height = 0
whiteboard_off_x = 0
whiteboard_off_y = 0
whiteboard_width = 0
window_name = "OpenCV-Whiteboard"

# Text properties
FONT = cv.FONT_HERSHEY_SIMPLEX
LINE_TYPE = cv.LINE_AA

# Button execution
cleared = None
loaded = None

# Function called when clicking the appropriate button
execute = ""

# Color variables
DARK_GRAY = (63, 63, 63)
GRAY = (127, 127, 127)
WHITE = (255, 255, 255)

color = None
color_key = 0
color_options = [
    ["Black", (0, 0, 0)],
    ["Blue", (255, 0, 0)],
    ["Green", (0, 255, 0)],
    ["Red", (0, 0, 255)]
]
color_label = color_options[0][0]
COLORS_NUMBER = len(color_options)
NUMBER_OF_COLOR_CHANNELS = 3

# Calculations
BUG_TOL = 50
COLOR_TOL = 25
ERASE_TOL = 40
HAND_INDICES = 21
SELECT_TOL = 40

# Image saving
FILE_FORMAT = ".jpg"
SEPARATOR = "_"

# Image variables
cam = None
cam_height = 480
cam_width = 640

exit_program = 0

SCALED_CAM = (480, 360)

w_screen = None
w_screen_cached = np.full((whiteboard_height, whiteboard_width, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)
w_screen_before_zoomed = None

# ----- Manipulation ----

# Draw
draw_end = None
draw_start = None
first_draw = True

# Save
first_save = True

# Color
first_color_change = True

# Hand tracking
latest_index_tip_position = []
scale = [0, 0]

# Button
first_append = True

# Zoom
first_zoom = True
first_in_zoom = True
in_zoom = False
off_height = 0
off_width = 0
zoom_factor = 100
zoom_initial_distance = 0

# Image filters
kernel_filter = True
kernel_gb = np.array([
    [1 / 9, 1 / 9, 1 / 9],
    [1 / 9, 1 / 9, 1 / 9],
    [1 / 9, 1 / 9, 1 / 9]
])
kernel_s = np.array([
    [0, -1, 0],
    [-1, 5, -1],
    [0, -1, 0]
])

# Mouse coordinates and interaction list
layers = []
mouse = [0, 0]

# ----- Mediapipe -----
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands


###################################################################################################
# FUNCTIONS                                                                                       #
###################################################################################################

def get_screen_resolution():
    """
    Get the resolution and offset of the primary monitor,
    as well as the scaling factor for the index fingertip point
    """
    global scale
    global whiteboard_height
    global whiteboard_off_x
    global whiteboard_off_y
    global whiteboard_width

    # Get the primary monitor values
    for m in si.get_monitors():
        if m.is_primary:
            whiteboard_width = m.width
            whiteboard_height = m.height
            whiteboard_off_x = m.x
            whiteboard_off_y = m.y

    # Set the scale according to width and height of whiteboard and capture device
    scale[0] = whiteboard_width / cam_width
    scale[1] = whiteboard_height / cam_height


def distance(pos1=None, pos2=None):
    """ Calculate the euclidean distance between two hand landmarks

    Keyword arguments:
        pos1    - hand landmark with x- and y-coordinates
        pos2    - hand landmark with x- and y-coordinates
    """
    return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)


def point_is_in_rectangle(coord=None, x=0, y=0, width=0, height=0):
    """ Calculate if a given point @ref coord is inside a given rectangle shaped area

    Keyword arguments:
        coord   - current mouse position
        x       - absolute x-offset of the rectangle according to the whiteboard screen
        y       - absolute y-offset of the rectangle according to the whiteboard screen
        width   - width of the rectangle
        height  - height of the rectangle
    """
    return (x <= coord[0] <= (x + width)) and (y <= coord[1] <= (y + height))


def setup_windows():
    """ Initialize global variables cam and w_screen for the capture device and the whiteboard screen """
    global cam
    global cam_width
    global cam_height
    global w_screen
    global whiteboard_off_x
    global whiteboard_off_y
    global window_name

    # Setup main window
    cv.namedWindow(window_name, cv.WND_PROP_FULLSCREEN)
    cv.setWindowProperty(window_name, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
    cv.moveWindow(window_name, whiteboard_off_x, whiteboard_off_y)
    cv.setMouseCallback(window_name, check_mouse_event)

    # Setup whiteboard screen
    clear_screen()

    # Setup capture device
    cam = cv.VideoCapture(-1)
    cam.set(cv.CAP_PROP_FRAME_WIDTH, cam_width)
    cam.set(cv.CAP_PROP_FRAME_HEIGHT, cam_height)

    # Setup buttons
    create_button("Save")
    create_button("Load")
    create_button("Clear")
    create_button("Exit")


def create_button(label="", size_x=125, size_y=50):
    """ Create button with label and size and append it to layers array

    Keyword arguments:
        label   - label of the button
        size_x  - width of the button
        size_y  - height of the button
    """
    global color_options
    global first_append
    global layers

    # Set initial colors
    btn = np.full((size_y, size_x, NUMBER_OF_COLOR_CHANNELS), color_options[0][1], np.uint8)
    btn[2:size_y - 2, 2:size_x - 2] = GRAY

    # Get boundary of text as well as x and y coordinates
    label_size = cv.getTextSize(label, FONT, 1, 2)[0]
    label_x = int((size_x - label_size[0]) / 2)
    label_y = int((size_y + label_size[1]) / 2)

    cv.putText(btn, label, (label_x, label_y), FONT, 1, WHITE, 2, LINE_TYPE)

    # Append buttons to layer array with additional x- and y-offset according to the main window
    if first_append:
        first_append = False
        layers.append([btn, 50, size_y, label])
    else:
        layers.append([btn, 50, layers[-1][2] + (size_y * 2) if layers else (size_y * 2), label])


def check_mouse_event(event=0, mouse_x=0, mouse_y=0, flags=None, userdata=None):
    """ Check for a mouse interaction in the main window

    Keyword arguments:
        event       - mouse event
        mouse_x     - x coordinate of current mouse position
        mouse_y     - y coordinate of current mouse position
        flags       - additional flags for mouse events
        userdata    - additional userdata
    """
    global cleared
    global execute
    global layers
    global mouse
    global w_screen
    global window_name

    # Analyze button highlighting for mouse movement
    if event == cv.EVENT_MOUSEMOVE:
        # Get current mouse position
        mouse[0] = mouse_x
        mouse[1] = mouse_y

        # Check if mouse hovers over button
        for lay in layers:
            if point_is_in_rectangle(mouse, lay[1], lay[2] + SCALED_CAM[1], lay[0].shape[1], lay[0].shape[0]):
                # Change appearance for highlighted button
                lay[0][2:lay[0].shape[0] - 2, 2:lay[0].shape[1] - 2] = DARK_GRAY
                execute = lay[3]
            else:
                # Set button to initial color state
                lay[0][2:lay[0].shape[0] - 2, 2:lay[0].shape[1] - 2] = GRAY

            # Put text on button again
            label_size = cv.getTextSize(lay[3], FONT, 1, 2)[0]
            label_x = int((lay[0].shape[1] - label_size[0]) / 2)
            label_y = int((lay[0].shape[0] + label_size[1]) / 2)

            cv.putText(lay[0], lay[3], (label_x, label_y), FONT, 1, WHITE, 2, LINE_TYPE)

    # Check if a button has been clicked
    if event == cv.EVENT_LBUTTONDOWN:
        if execute == "Save":
            save_screen()
        if execute == "Load":
            load_image()
        if execute == "Clear":
            cleared = np.full((whiteboard_height, whiteboard_width, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)
        if execute == "Exit":
            release_variables()

        execute = ""


def release_variables():
    """ Release allocated variables """
    global cam

    cam.release()
    cv.destroyAllWindows()


def show_window(capture=None, index_coord=None, gesture="", col=color_options[0][1]):
    """ Display image in a single window

    Keyword arguments:
        capture     - captured frame of camera device
        index_coord - coordinate of index fingertip
        gesture     - current gesture calculated
        col         - current color label
    """
    global cleared
    global exit_program
    global layers
    global loaded
    global w_screen
    global w_screen_cached
    global w_screen_before_zoomed
    global window_name
    global zoom_factor

    # Check if an image was loaded
    if loaded is not None:
        w_screen = copy.deepcopy(loaded)
        w_screen_before_zoomed = copy.deepcopy(w_screen)
        loaded = None
        zoom_factor = 100

    # Check if the image was cleared
    if cleared is not None:
        w_screen = copy.deepcopy(cleared)
        w_screen_before_zoomed = copy.deepcopy(w_screen)
        cleared = None
        zoom_factor = 100

    # Create a deep copy of the whiteboard screen
    w_screen_cached = copy.deepcopy(w_screen)

    # Modify capture frame
    capture = cv.cvtColor(capture, cv.COLOR_RGB2BGR)
    capture = cv.flip(capture, 1)
    capture = cv.putText(capture, "Gesture: " + gesture, (20, 460), FONT, 0.75, color_options[0][1], 2, LINE_TYPE)
    capture = cv.putText(capture, "Gesture: " + gesture, (20, 460), FONT, 0.75, color_options[2][1], 1, LINE_TYPE)
    capture = cv.putText(capture, "Color: " + col, (300, 460), FONT, 0.75, color_options[0][1], 2, LINE_TYPE)
    capture = cv.putText(capture, "Color: " + col, (300, 460), FONT, 0.75, color_options[2][1], 1, LINE_TYPE)
    capture = cv.putText(capture, "Zoom: " + str(zoom_factor), (20, 260), FONT, 0.75, color_options[0][1], 2, LINE_TYPE)
    capture = cv.putText(capture, "Zoom: " + str(zoom_factor), (20, 260), FONT, 0.75, color_options[2][1], 1, LINE_TYPE)
    capture = cv.resize(capture, SCALED_CAM, 0, 0, interpolation=cv.INTER_CUBIC)

    # Mark the index fingertip position on the screen if existent
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


def calc_hand_rotation_angle(lmx_n, lmy_n, offset):
    """ Calculate the hand rotation angle according to the current hand landmarks

    Keyword arguments:
        lmx_n   - hand landmark x coordinates
        lmy_n   - hand landmark y coordinates
        offset  - statically given offset
    """
    off = 21 * offset

    # Calculate angle
    ang = math.acos(abs(lmy_n[5 + off] - lmy_n[0 + off]) / abs(
        math.sqrt((lmy_n[5 + off] - lmy_n[0 + off]) ** 2 + (lmx_n[5 + off] - lmx_n[0 + off]) ** 2)))

    # Rotation over 90°
    if lmy_n[0 + off] < lmy_n[5 + off]:
        ang = math.pi / 2 + (math.pi / 2 - ang)

    # Rotation anticlockwise
    if lmx_n[0 + off] < lmx_n[5 + off]:
        ang *= -1

    # Offset for left or right hand

    # Up
    if abs(ang) <= .25 * math.pi:
        if lmx_n[5 + off] > lmx_n[17 + off]:
            ang += .5
        else:
            ang -= .5

    # Right
    elif .25 * math.pi < ang < .75 * math.pi:
        if lmy_n[5 + off] < lmy_n[17 + off]:
            ang += .5
        else:
            ang -= .5

    # Down
    elif abs(ang) >= .75 * math.pi:
        if lmx_n[5 + off] < lmx_n[17 + off]:
            ang += .5
        else:
            ang -= .5

    # Left
    elif -.25 * math.pi > ang > -.75 * math.pi:
        if lmy_n[5 + off] > lmy_n[17 + off]:
            ang += .5
        else:
            ang -= .5

    return ang


def check_user_gesture(landmarks=None):
    """ Check the image for a hand gesture and distinguish between them

    Keyword arguments:
        landmarks - hand landmarks
    """
    draw_flag = False
    select_flag = False
    erase_flag = False
    color_flag = False
    zoom_flag = False

    # Split x and y coordinates into two separate arrays
    lm = np.array(landmarks)
    lmx_n, lmy_n = zip(*lm)

    # Arrays for separate x and y coordinates
    lmx = []
    lmy = []

    # Rotation
    ang0 = calc_hand_rotation_angle(lmx_n, lmy_n, 0)

    for i in range(21):
        x = lmx_n[i]
        y = lmy_n[i]
        lmx.append(math.cos(ang0) * x - math.sin(ang0) * y)
        lmy.append(math.sin(ang0) * x + math.cos(ang0) * y)

    if len(lmx_n) > 21:
        ang1 = calc_hand_rotation_angle(lmx_n, lmy_n, 1)
        for i in range(21, 42):
            x = lmx_n[i]
            y = lmy_n[i]
            lmx.append(math.cos(ang1) * x - math.sin(ang1) * y)
            lmy.append(math.sin(ang1) * x + math.cos(ang1) * y)

    # Check if only one hand has been listed
    if len(lm) != 42:
        # Gesture: DRAW
        for e in lmy[:6] + lmy[9:HAND_INDICES]:
            if e > lmy[6]:
                draw_flag = True
            else:
                draw_flag = False
                break

        # Gesture: SELECT
        if draw_flag:
            if distance(lm[4], lm[6]) > SELECT_TOL:
                draw_flag = False
                select_flag = True

        # Gesture SELECT COLOR
        for e in lmy[:12] + lmy[13:HAND_INDICES]:
            if e > lmy[12] and distance(lm[8], lm[12]) < COLOR_TOL:
                color_flag = True
            else:
                color_flag = False
                break

        # Gesture: ERASE
        if color_flag and distance(lm[4], lm[5]) < ERASE_TOL:
            erase_flag = True

    # Otherwise, check for a two hand interaction
    else:
        # Gesture: ZOOM
        if distance(lm[0], lm[HAND_INDICES]) > BUG_TOL:
            if distance(lm[4], lm[8]) > 50 and distance(lm[HAND_INDICES + 4], lm[HAND_INDICES + 8]) > 50:
                for e, f in zip(lmy[:6] + lmy[9:HAND_INDICES],
                                lmy[HAND_INDICES:HAND_INDICES + 6] + lmy[HAND_INDICES + 9:]):
                    if e > lmy[6] and f > lmy[HAND_INDICES + 6]:
                        zoom_flag = True
                    else:
                        zoom_flag = False
                        break

    # Return gesture according to set flags
    if draw_flag:
        return "draw"
    if select_flag:
        return "select"
    if erase_flag:
        return "erase"
    if color_flag:
        # Gesture: SWITCH COLOR
        if lmy[16] < lmy[14] and lmy[20] < lmy[18]:
            return "switch color"
        return "select color"
    if zoom_flag:
        return "zoom"

    return "unknown"


def determine_right_left(landmarks=None):
    """ Rearrange the order of the hand landmarks to be right hand first

    Keyword arguments:
        landmarks - hand landmarks
    """
    if len(landmarks) == HAND_INDICES * 2:
        if landmarks[5][0] < landmarks[17][0]:
            landmarks_left = landmarks[:HAND_INDICES]
            landmarks_right = landmarks[HAND_INDICES:]
            return landmarks_right + landmarks_left

    return landmarks


def restore_screen():
    """ Reset the screen to the latest change before adding custom layers """
    global w_screen
    global w_screen_cached
    w_screen = copy.deepcopy(w_screen_cached)


def draw(coord=None, col=color, thickness=2):
    """ Responsible for drawing the users input

    Keyword arguments:
        coord       - current index fingertip position
        col         - selected color
        thickness   - thickness of the drawn line

    first_draw: flag is set to True, if the draw function has been called the first time
    draw_start: starting point of the line
    draw_end:   end point of the line
    """
    global draw_end
    global draw_start
    global first_draw
    global w_screen
    global w_screen_before_zoomed
    global whiteboard_width
    global whiteboard_height
    global zoom_factor

    if first_draw:
        first_draw = False
        draw_start = coord
        draw_end = None
    else:
        draw_end = coord
        w_screen = cv.line(w_screen, draw_start, draw_end, col, thickness=thickness, lineType=LINE_TYPE)
        draw_start = draw_end

        if zoom_factor == 100:
            w_screen_before_zoomed = copy.deepcopy(w_screen)


def switch_color():
    """ Switch the current color, if the applicable gesture is called """
    global color
    global color_key
    global color_label
    global color_options
    global first_color_change

    if first_color_change:
        first_color_change = False
        if color_key + 1 < COLORS_NUMBER:
            color_key += 1
        else:
            color_key = 0

    color = color_options[color_key][1]
    color_label = color_options[color_key][0]


def zoom(lm=None):
    """ Perform a zoom on the whiteboard screen

    Keyword arguments:
        lm  - hand landmarks
    """
    global first_zoom
    global first_in_zoom
    global in_zoom
    global off_width
    global off_height
    global scale
    global w_screen
    global w_screen_before_zoomed
    global whiteboard_height
    global whiteboard_width
    global zoom_initial_distance
    global zoom_factor

    # Calculate the distance between the two index fingertips
    i1 = [round(a * b) for a, b in zip(lm[8], scale)]
    i2 = [round(a * b) for a, b in zip(lm[HAND_INDICES + 8], scale)]
    index_distance = distance(i1, i2)

    # If not in zoom mode set the initial distance to index distance
    if not in_zoom:
        if first_zoom:
            first_zoom = False
            zoom_initial_distance = int(index_distance)

    # Otherwise, calculate the appropriate initial distance to get the current @ref zoom_factor
    else:
        if first_in_zoom:
            first_in_zoom = False
            zoom_initial_distance = int(zoom_factor * index_distance / 100)

    zoom_factor = int(zoom_initial_distance * 100 / index_distance)

    # Cap zoom_factor for special cases
    if zoom_factor > 100:
        zoom_factor = 100

    if zoom_factor < 1:
        zoom_factor = 1

    if zoom_factor == 100:
        in_zoom = False

    factor = zoom_factor / 100

    # Calculate the relative resolution according to the zoom factor
    height = int(whiteboard_height * factor)
    off_height = int((whiteboard_height - height) / 2)
    width = int(whiteboard_width * factor)
    off_width = int((whiteboard_width - width) / 2)

    # Set the whiteboard screen to that specific relative resolution and resize it to the intended fullscreen resolution
    w_screen = copy.deepcopy(
        w_screen_before_zoomed[off_height:whiteboard_height - off_height, off_width:whiteboard_width - off_width]
    )
    w_screen = cv.resize(w_screen, (whiteboard_width, whiteboard_height), interpolation=cv.INTER_AREA)


def save_screen():
    """ Save whiteboard screen """
    global w_screen_cached

    # Create the sub folder, if it does not exist
    sub_folder = "/Saves"
    path = os.getcwd() + sub_folder
    try:
        access_mode = 0o755
        os.mkdir(path=path, mode=access_mode)
    except FileExistsError:
        pass

    # Show file dialog for writing the whiteboard screen image with a valid filename
    tkinter.Tk().withdraw()
    filename = fd.asksaveasfilename(defaultextension="", initialdir=path, filetypes=[("Images", ".jpg")])

    if filename:
        cv.imwrite(filename, cv.flip(w_screen_cached, 1))


def backup_screen():
    """ Make a backup of the image in case of an application error """
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
    global loaded
    global w_screen_cached
    global whiteboard_height
    global whiteboard_width

    # Create the sub folder, if it does not exist
    sub_folder = "/Saves"
    path = os.getcwd() + sub_folder
    try:
        access_mode = 0o755
        os.mkdir(path=path, mode=access_mode)
    except FileExistsError:
        pass

    # Show file dialog for loading an image
    tkinter.Tk().withdraw()
    filename = fd.askopenfilename(initialdir=path)
    try:
        loaded = cv.flip(cv.imread(filename), 1)
    except TypeError:
        pass

    # Check if loaded image has the same resolution as whiteboard, if not resize the loaded image
    if loaded is not None:
        # Get the resolution of the loaded image
        loaded_height, loaded_width, _ = loaded.shape
        if loaded_height != whiteboard_height or loaded_width != whiteboard_width:
            loaded = cv.resize(loaded, (whiteboard_width, whiteboard_height), interpolation=cv.INTER_AREA)
            w_screen_cached = copy.deepcopy(loaded)


def clear_screen():
    """ Get a new blank whiteboard screen """
    global w_screen
    global w_screen_before_zoomed
    w_screen = np.full((whiteboard_height, whiteboard_width, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)
    w_screen_before_zoomed = np.full((whiteboard_height, whiteboard_width, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)


def run():
    """ LOOP FUNCTION

    Calculate the 21 hand coordinates for tracking.
    Also manage settings for different user webcam input.
    """
    global cam
    global color
    global color_label
    global first_color_change
    global first_draw
    global first_in_zoom
    global first_save
    global first_zoom
    global in_zoom
    global kernel_filter
    global mp_drawing
    global mp_drawing_styles
    global mp_hands
    global off_height
    global off_width
    global scale
    global w_screen
    global w_screen_before_zoomed
    global zoom_factor

    with mp_hands.Hands(
            max_num_hands=2,
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
    ) as hands:
        # If capture device has been initialized successfully and exit key "q" has not been pressed
        while cam.isOpened() and not exit_program:
            # Read from the camera
            success, frame = cam.read()

            # Make a backup
            if not success:
                print("Could not read correctly from open cameras!")
                backup_screen()
                print("Backup for whiteboard has been made!")
                break

            # Convert to RGB
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

            # Get hand landmarks of current frame
            results = hands.process(frame)
            gesture = "unknown"
            scaled_index_tip = None

            if results.multi_hand_landmarks:
                # Array for hand landmarks
                landmarks = []
                for hand_landmarks in results.multi_hand_landmarks:
                    for lm in hand_landmarks.landmark:
                        # Adjust hand gesture coordinates to absolute frame values instead of a value between 0 and 1
                        lmx = int(lm.x * cam_width)
                        lmy = int(lm.y * cam_height)
                        landmarks.append([lmx, lmy])

                    # Draw the connections between the landmarks
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style()
                    )

                # Rearrange the order of the hand landmarks
                landmarks = determine_right_left(landmarks)

                # Set index fingertip position
                index_tip = landmarks[8]

                # Scale index fingertip position according to the scaling factor
                scaled_index_tip = [round(a * b) for a, b in zip(index_tip, scale)]

                # Check gesture
                gesture = check_user_gesture(landmarks)

                # Filter function according to gesture calculation output
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

                if gesture == "zoom":
                    if in_zoom:
                        # Check if the user has edited the displayed whiteboard screen
                        w_shown = cv.resize(
                            w_screen,
                            (whiteboard_width - off_width * 2, whiteboard_height - off_height * 2)
                        )
                        w_saved = w_screen_before_zoomed[
                                  off_height:whiteboard_height - off_height,
                                  off_width:whiteboard_width - off_width
                                  ]

                        # Whiteboard screen has been edited
                        if not np.array_equal(w_shown, w_saved):
                            w_screen_tmp = copy.deepcopy(
                                cv.resize(
                                    w_screen,
                                    (whiteboard_width - int(off_width * 2), whiteboard_height - int(off_height * 2))
                                )
                            )
                            w_screen_before_zoomed[
                                off_height:whiteboard_height - off_height,
                                off_width:whiteboard_width - off_width
                            ] = copy.deepcopy(w_screen_tmp)

                            # Put a sharpening (and smoothen) filter on the image
                            if kernel_filter:
                                kernel_filter = False

                                # Sharpen the image
                                w_screen_before_zoomed = copy.deepcopy(
                                    cv.filter2D(src=w_screen_before_zoomed, ddepth=-1, kernel=kernel_s)
                                )

                                # Smoothen image
                                # # Gaussian blur the image
                                # w_screen_before_zoomed = copy.deepcopy(
                                #     cv.filter2D(src=w_screen_before_zoomed, ddepth=-1, kernel=kernel_gb)
                                # )

                    # Execute the image zoom
                    zoom(landmarks)
                else:
                    # Reset flags for certain scenarios
                    first_zoom = True
                    first_in_zoom = True
                    if zoom_factor != 100:
                        in_zoom = True
                    else:
                        kernel_filter = True

            # Show the whiteboard screen, camera and all extensions in the main window
            show_window(frame, scaled_index_tip, gesture, color_label)

            # Restore the whiteboard screen after editing with different layers
            restore_screen()


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
