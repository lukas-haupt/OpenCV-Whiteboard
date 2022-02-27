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
WIDTH = 640
HEIGHT = 480
NUMBER_OF_COLOR_CHANNELS = 3
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
SPACER = np.full((HEIGHT, 2, NUMBER_OF_COLOR_CHANNELS), BLACK, np.uint8)
FONT = cv.FONT_HERSHEY_SIMPLEX
LINE_TYPE = cv.LINE_AA
HAND_INDICES = 21
SEPARATOR = "_"
FILE_FORMAT = ".jpg"
SELECT_TOLERANCE = 40
ERASE_TOLERANCE = 20

cam = None
w_screen = None
w_screen_cached = np.full((HEIGHT, WIDTH, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)
exit_program = 0

# Variables for drawing a line
first_draw = True
draw_start = None
draw_end = None

# Variable for current index fingertip position
latest_index_tip_position = []

# Mediapipe variables for drawing hand tracking coordinates
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands


def distance(coord1=None, coord2=None):
    """ Calculate the euclidean distance between two hand landmarks """
    return math.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)


def setup_windows():
    """ Initialize global variables cam and w_screen for the capture device and the white screen """
    global cam
    global w_screen

    w_screen = np.full((HEIGHT, WIDTH, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)
    cam = cv.VideoCapture(-1)
    cam.set(cv.CAP_PROP_FRAME_WIDTH, WIDTH)
    cam.set(cv.CAP_PROP_FRAME_HEIGHT, HEIGHT)


def release_variables():
    """ Release allocated variables """
    global cam

    cam.release()
    cv.destroyAllWindows()


def show_windows(capture=None, screen=None, gesture=None):
    """ Display images in a single window """
    global exit_program

    capture = cv.cvtColor(capture, cv.COLOR_RGB2BGR)
    capture = cv.flip(capture, 1)
    capture = cv.putText(capture, "Gesture: " + gesture, (20, 460), FONT, 0.75, BLACK, 2, LINE_TYPE)
    capture = cv.putText(capture, "Gesture: " + gesture, (20, 460), FONT, 0.75, GREEN, 1, LINE_TYPE)
    screen = cv.flip(screen, 1)
    cv.imshow("AI Whiteboard", np.hstack((capture, SPACER, screen)))
    if cv.waitKey(1) == ord("q"):
        exit_program = 1
    reverse_current_finger_tip_position()


def check_user_gesture(landmarks=None):
    """ Check the image for a hand gesture and distinguish between them """
    draw_flag = False
    select_flag = False
    erase_flag = False
    save_flag = False
    clear_flag = False

    # Split x and y coordinates into two separate arrays
    lm = np.array(landmarks)
    lmx, lmy = zip(*lm)

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
    return "unknown"


def show_current_index_tip_position(coord=None, color=BLACK):
    """ Set a circle around the index fingertip on the screen, so that the current position is shown """
    global w_screen
    global w_screen_cached
    w_screen_cached = copy.deepcopy(w_screen)

    if coord is not None:
        w_screen = cv.circle(w_screen, center=coord, radius=3, color=color, thickness=1, lineType=LINE_TYPE)


def reverse_current_finger_tip_position():
    """ Reset the screen to the latest change before adding the index fingertip circle """
    global w_screen
    global w_screen_cached
    w_screen = copy.deepcopy(w_screen_cached)


def draw(coord=None, color=BLACK, thickness=2):
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
        w_screen = cv.line(w_screen, draw_start, draw_end, color, thickness=thickness, lineType=LINE_TYPE)
        draw_start = draw_end


def save_screen():
    """ Save the current whiteboard screen into a subdirectory """
    global w_screen

    # Create the sub folder, if it does not exist
    sub_folder = "/Saves"
    path = os.getcwd() + sub_folder
    try:
        access_mode = 0o755
        os.mkdir(path=path, mode=access_mode, )
    except FileExistsError:
        pass

    # Get current date
    current_date = dt.datetime.now()
    date_str = SEPARATOR.join(("", str(current_date.year), str(current_date.month), str(current_date.day)))

    # Save w_screen
    filename = "savedImage" + date_str + FILE_FORMAT
    cv.imwrite(os.path.join(path, filename), cv.flip(w_screen, 1))


def clear_screen():
    """ Get a new blank whiteboard screen """
    global w_screen
    w_screen = np.full((HEIGHT, WIDTH, NUMBER_OF_COLOR_CHANNELS), WHITE, np.uint8)


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
            index_tip = None

            if results.multi_hand_landmarks:
                # Array for gesture prediction
                landmarks = []
                for hand_landmarks in results.multi_hand_landmarks:
                    for lm in hand_landmarks.landmark:
                        # Adjust hand gesture coordinates to absolute frame values
                        lmx = int(lm.x * WIDTH)
                        lmy = int(lm.y * HEIGHT)
                        landmarks.append([lmx, lmy])

                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style()
                    )

                index_tip = landmarks[8]
                gesture = check_user_gesture(landmarks)

                if gesture == "draw":
                    draw(index_tip, BLACK, 2)
                elif gesture == "erase":
                    draw(index_tip, WHITE, 20)
                else:
                    first_draw = True

                if gesture == "save":
                    save_screen()
                if gesture == "clear":
                    clear_screen()

            show_current_index_tip_position(index_tip)
            show_windows(frame, w_screen, gesture)


###################################################################################################
# MAIN FUNCTION                                                                                   #
###################################################################################################
def main():
    setup_windows()
    run()
    release_variables()


if __name__ == "__main__":
    main()
