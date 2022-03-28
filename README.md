# OpenCV-Whiteboard

## Description

In this application a user can use the basic functionality of a whiteboard.

With the hand gesture input to the webcam, functions like drawing, erasing, 
<br>
saving and clearing an image can be executed.

More extensions to follow.

Mediapipe is used to track hand movements, OpenCV for hand gesture recognition and image manipulation.
<br>
For more information see requirements.txt

## Installation and execution

### Jetson Nano

1. Update System
```console
sudo apt update
sudo apt upgrade
sudo apt install python3-pip curl
pip3 install --upgrade pip
```

2. Download Mediapipe OpenCV install script (~550 MiB).
```console
git clone https://github.com/google/mediapipe.git
```

3. Execute OpenCV install script. </br>
This process will take about one hour.
```console
cd mediapipe
chmod u+x setup_opencv.sh
sudo ./setup_opencv.sh
```

4. Download (~500 MiB) and install mediapipe wheel
```console
cd
git clone https://github.com/PINTO0309/mediapipe-bin.git && cd mediapipe-bin
chmod u+x ./v0.8.5/download.sh && ./v0.8.5/download.sh
unzip v0.8.5.zip
sudo pip3 install v0.8.5/numpy119x/py36/mediapipe-0.8.5_cuda102-cp36-cp36m-linux_aarch64.whl dataclasses
```

5. Clone Repo
```console
git clone -b jetson-webcam git@github.com:lukas-haupt/OpenCV-Whiteboard.git
cd OpenCV-Whiteboard
sudo pip3 install -r requirements.txt
python3 opencv-whiteboard.py
```

### Other systems

1. Clone repository: ```git clone```
2. Switch to folder: ```cd OpenCV-Whiteboard```
3. Install requirements: ```pip install -r requirements.txt```
4. Execute: ```python3 opencv-whiteboard.py```
