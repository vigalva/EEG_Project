from keras.models import model_from_json
import scipy.io
import numpy as np
import pandas as pd

from tkinter import *
import math
import time
import asyncio
from lib.cortex import Cortex
import json
import keyboard

json_file = open('./test/model.json', 'r')
loaded_model_json = json_file.read()
json_file.close()
model = model_from_json(loaded_model_json)
# load weights into new model
model.load_weights("./test/model.h5")
print("Loaded model from disk")
model.compile(loss='binary_crossentropy',
              optimizer='rmsprop',
              metrics=['accuracy'])

numChannels = 14
sliceSize = 127
cortex = Cortex('./cortex_creds')

async def start(cortex):
    await cortex.inspectApi()
    # print("** USER LOGIN **")
    # await cortex.get_user_login()
    # print("** GET CORTEX INFO **")
    # await cortex.get_cortex_info()
    # print("** HAS ACCESS RIGHT **")
    # await cortex.has_access_right()
    # print("** REQUEST ACCESS **")
    await cortex.request_access()
    # print("** AUTHORIZE **")
    await cortex.authorize()
    # print("** GET LICENSE INFO **")
    # await cortex.get_license_info()
    # print("** QUERY HEADSETS **")
    await cortex.query_headsets()
    # print("** CREATE SESSION **")
    await cortex.create_session(activate=True,
                          headset_id=cortex.headsets[0])
    # print("** SUBSCRIBE EEG **")
    await cortex.subscribe(['eeg'])

async def getDataFromHeadSet(cortex):
    data = await cortex.get_data()
    data_dic = json.loads(data)
    # print(data_dic)
    return data_dic["eeg"][2:16]

async def closeCortex(cortex):
    await cortex.close_session()
    await cortex.close()


def get_next_point_in_movement(num, up_or_down):
    if up_or_down == True:
        return -math.sqrt(73 ** 2 - (num - 175) ** 2) + 225

    else:
        return math.sqrt(73 ** 2 - (num - 175) ** 2) + 225


def animation(canvas, left_hand, right_hand, result,y_move_left,y_move_right,y_left_mod,y_right_mod):
    if result == 1:
        # time.sleep(0.002)
        canvas.coords(left_hand, 225, 175, get_next_point_in_movement(y_move_left, True), y_move_left)
        canvas.coords(right_hand, 225, 175, 280, 221)
        if y_move_left == 150:
            y_left_mod = +1
        elif y_move_left == 220:
            y_left_mod = -1
        y_move_left = y_move_left + y_left_mod
        canvas.update()

    elif result == 2:
        # time.sleep(0.002)
        canvas.coords(left_hand, 225, 175, 170, 221)
        canvas.coords(right_hand, 225, 175, get_next_point_in_movement(y_move_right, False), y_move_right)
        if y_move_right == 150:
            y_right_mod = +1
        elif y_move_right == 220:
            y_right_mod = -1
        y_move_right = y_move_right + y_right_mod
        canvas.update()
    else:
        # time.sleep(0.002)
        canvas.coords(left_hand, 225, 175, 170, 221)
        canvas.coords(right_hand, 225, 175, 280, 221)
        y_move_right = 221
        y_move_left = 221
        y_left_mod = -1
        y_right_mod = -1
        canvas.update()
    canvas.pack()
    return y_move_left,y_move_right,y_left_mod,y_right_mod


def createDrawing():
    root = Tk()
    root.title('Canvas')
    canvas = Canvas(root, width=450, height=450)
    head = canvas.create_oval(200, 100, 250, 150, fill='gray90')
    body = canvas.create_line(225, 150, 225, 300)

    left_hand = canvas.create_line(225, 175, 170, 221)
    right_hand = canvas.create_line(225, 175, 280, 221)
    left_leg = canvas.create_line(225, 300, 170, 348)
    right_leg = canvas.create_line(225, 300, 280, 348)
    canvas.pack()
    return canvas, left_hand, right_hand,root

loop = asyncio.get_event_loop()
loop.run_until_complete(start(cortex))
#Model predict
canvas,left_hand,right_hand,root=createDrawing()
slicedTestData=[[0]*numChannels]*sliceSize
slicedTestData=np.asarray(slicedTestData)
# resultDict={1:0,2:0,0:0}
y_move_left,y_move_right,y_left_mod,y_right_mod = animation(canvas,left_hand,right_hand,0,221,221,-1,-1)
while True:
    loop = asyncio.get_event_loop()
    dataEEGarray = loop.run_until_complete(getDataFromHeadSet(cortex))
    slicedTestData=np.concatenate((slicedTestData,[dataEEGarray]))
    slicedTestData = slicedTestData[1:]
    predictionData=np.asarray([slicedTestData])
    prediction=model.predict(predictionData, batch_size=64)
    result=np.argmax(prediction)+1
    y_move_left,y_move_right,y_left_mod,y_right_mod = animation(canvas,left_hand,right_hand,result,y_move_left,y_move_right,y_left_mod,y_right_mod)
    # resultDict[result]=resultDict[result]+1
    if keyboard.is_pressed('space'):
        root.destroy()
        break


loop = asyncio.get_event_loop()
loop.run_until_complete(closeCortex(cortex))




