#!/usr/bin/env python

from tkinter import Tk, StringVar, Button, Label
from queue import SimpleQueue
from random import randint
from math import floor
import time
import cv2
import pyfakewebcam
import numpy as np
import keyboard
import sys
import os


HEIGHT = 720
WIDTH = 1280

rgb_frame = None
abs_frame_index = 0
init_frame_index = 0

freeze = False
freeze_frame = None

pre_camouflage = False
camouflage = False
freezed_window = []


window = []
n_frames = 60
cur_frame = n_frames - 1

queue = SimpleQueue()


def init_freeze():
    global freeze
    global freeze_frame

    freeze_frame = rgb_frame
    freeze = not freeze


def init_camouflage():
    global camouflage
    global pre_camouflage
    global init_frame_index
    global queue

    if not camouflage:
        time.sleep(1)
        pre_camouflage = True
        init_frame_index = abs_frame_index
    else:
        counter_label_text.set("")
        queue = SimpleQueue()
        camouflage = False



def init_gui():
    global gui
    global counter_label_text

    gui = Tk()
    gui.geometry("130x100")

    freeze_btn_text = StringVar()
    freeze_btn = Button(gui, textvariable=freeze_btn_text, command=init_freeze)
    freeze_btn_text.set("Freeze")
    freeze_btn.pack()

    camouflage_btn_text = StringVar()
    camouflage_btn = Button(gui, textvariable=camouflage_btn_text, command=init_camouflage)
    camouflage_btn_text.set("Camouflage")
    camouflage_btn.pack()

    counter_label_text = StringVar()
    counter_label = Label(gui, textvariable=counter_label_text)
    counter_label.pack()


def loop():
    global cur_frame
    global freeze_frame
    global rgb_frame
    global abs_frame_index
    global camouflage
    global pre_camouflage
    global freezed_window
    global queue

    # update gui
    if pre_camouflage and (abs_frame_index - init_frame_index < n_frames):
        counter_label_text.set(f"Stai fermo per {abs_frame_index - init_frame_index}/{n_frames}")
    elif pre_camouflage:
        cur_frame = n_frames - 1
        freezed_window = window.copy()
        counter_label_text.set("ATTIVO!")
        pre_camouflage = False
        camouflage = True

    try:
        gui.update_idletasks()
        gui.update()
    except:
        return

    # obtain the frame from the camera
    ret, frame = camera_cap.read()
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # update the sliding window
    if len(window) < n_frames:
        window.append(rgb_frame)
    else:
        del window[0]
        window.append(rgb_frame)

    # camouflage mode
    if camouflage:

        if queue.empty():
            # choose whether to go backwards
            if cur_frame != 0 and cur_frame != (n_frames - 1):
                backwards = randint(0, 1)
            else:
                backwards = cur_frame # choose only what you can do

            # get a random length without exiting window limits, and then fill the queue
            if backwards:
                length = randint(floor(1/4*n_frames), n_frames) % (cur_frame + 1)
                for i in range(cur_frame, cur_frame - length - 1, -1):
                    queue.put(i)
            else:
                length = randint(floor(1/4*n_frames), 120) % (n_frames - cur_frame + 1)
                for i in range(cur_frame, cur_frame + length):
                    queue.put(i)

        # display the first frame in the queue
        try:
            cur_frame = queue.get(timeout=0.1)
        except:
            pass
        fake_camera.schedule_frame(freezed_window[cur_frame])

    # freezed mode
    elif freeze:
        fake_camera.schedule_frame(freeze_frame)

    # normal mode
    else:
        fake_camera.schedule_frame(rgb_frame)

    abs_frame_index += 1


if __name__ == "__main__":

    if len(sys.argv) == 1:
        print("Please specify the path of the dummy camera!", file=sys.stderr)
        exit(1)

    elif len(sys.argv) == 5:
        WIDTH = int(sys.argv[3])
        HEIGHT = int(sys.argv[4])


    camera_cap = cv2.VideoCapture(int(sys.argv[1]))
    fake_camera = pyfakewebcam.FakeWebcam("/dev/video"+sys.argv[2], WIDTH, HEIGHT)

    init_gui()

    while True:
        #if keyboard.is_pressed("ctrl"):
            #init_camouflage()
        loop()
