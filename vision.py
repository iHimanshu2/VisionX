import os
import argparse
import cv2
import numpy as np
import sys
import time
from threading import Thread
import importlib.util
import json


class VideoStream:

    def __init__(self,resolution=(640,480),framerate=30):
        self.stream = cv2.VideoCapture(0)
        ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])


        (self.grabbed, self.frame) = self.stream.read()


        self.stopped = False

    def start(self):

        Thread(target=self.update,args=()).start()
        return self

    def update(self):

        while True:

            if self.stopped:
                self.stream.release()
                return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True


parser = argparse.ArgumentParser()
parser.add_argument('--modeldir', help='Folder the .tflite file is located in',
                    required=True)
parser.add_argument('--graph', help='Name of the .tflite file, if different than detect.tflite',
                    default='detect.tflite')
parser.add_argument('--labels', help='Name of the labelmap file, if different than labelmap.txt',
                    default='labelmap.txt')
parser.add_argument('--threshold', help='Minimum confidence threshold for displaying detected objects',
                    default=0.5)
parser.add_argument('--resolution', help='Desired webcam resolution in WxH. If the webcam does not support the resolution entered, errors may occur.',
                    default='1280x720')
parser.add_argument('--edgetpu', help='Use Coral Edge TPU Accelerator to speed up detection',
                    action='store_true')

args = parser.parse_args()

model = args.modeldir
graph_name = args.graph
labelmapname = args.labels
minimum_threshold = float(args.threshold)
resW, resH = args.resolution.split('x')
imW, imH = int(resW), int(resH)
use_TPU = args.edgetpu


pkg = importlib.util.find_spec('tensorflow')
if pkg is None:
    from tflite_runtime.interpreter import Interpreter
    if use_TPU:
        from tflite_runtime.interpreter import load_delegate
else:
    from tensorflow.lite.python.interpreter import Interpreter
    if use_TPU:
        from tensorflow.lite.python.interpreter import load_delegate

if use_TPU:
    if (graph_name == 'detect.tflite'):
        graph_name = 'edgetpu.tflite'

CWD_PATH = os.getcwd()

PATH_TO_CKPT = os.path.join(CWD_PATH,model,graph_name)

PATH_TO_LABELS = os.path.join(CWD_PATH,model,labelmapname)

with open(PATH_TO_LABELS, 'r') as f:
    labels = [line.strip() for line in f.readlines()]

if labels[0] == '???':
    del(labels[0])


if use_TPU:
    interpreter = Interpreter(model_path=PATH_TO_CKPT,
                              experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
    print(PATH_TO_CKPT)
else:
    interpreter = Interpreter(model_path=PATH_TO_CKPT)

interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
height = input_details[0]['shape'][1]
width = input_details[0]['shape'][2]

floating_model = (input_details[0]['dtype'] == np.float32)

input_mean = 127.5
input_std = 127.5


frame_rate_calc = 1
freq = cv2.getTickFrequency()


videostream = VideoStream(resolution=(imW,imH),framerate=30).start()
time.sleep(1)

font = cv2.FONT_HERSHEY_SIMPLEX
IM_WIDTH = imW
IM_HEIGHT = imH


left_topleft = (int(IM_WIDTH*0),int(IM_HEIGHT*0))
left_bottomright = (int(IM_WIDTH*0.33),int(IM_HEIGHT))


middle_topleft = (int(IM_WIDTH*0.34),int(IM_HEIGHT*0))
middle_bottomright = (int(IM_WIDTH*0.66),int(IM_HEIGHT))


right_topleft = (int(IM_WIDTH*0.67),int(IM_HEIGHT*0))
right_bottomright = (int(IM_WIDTH),int(IM_HEIGHT))



while True:
    t1 = cv2.getTickCount()
    frame1 = videostream.read()

    fp = open("/home/pi/textrecognitionstatus.txt", "r+")
    text_status = fp.read()
    if text_status == "True":
        fp.seek(0)
        fp.write("False")
        cv2.imwrite("text.png", frame1)
    fp.close()

    frame = frame1.copy()
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_resized = cv2.resize(frame_rgb, (width, height))
    input_data = np.expand_dims(frame_resized, axis=0)

    if floating_model:
        input_data = (np.float32(input_data) - input_mean) / input_std

    interpreter.set_tensor(input_details[0]['index'],input_data)
    interpreter.invoke()

    boxes = interpreter.get_tensor(output_details[0]['index'])[0]
    classes = interpreter.get_tensor(output_details[1]['index'])[0]
    scores = interpreter.get_tensor(output_details[2]['index'])[0]
    #num = interpreter.get_tensor(output_details[3]['index'])[0]

    cv2.rectangle(frame,right_topleft,right_bottomright,(255,20,20),3)
    cv2.putText(frame,"Left box",(right_topleft[0]+10,right_topleft[1]-10),font,1,(255,20,255),3,cv2.LINE_AA)
    cv2.rectangle(frame,middle_topleft,middle_bottomright,(20,255,20),3)
    cv2.rectangle(frame,left_topleft,left_bottomright,(20,20,255),3)
    cv2.putText(frame,"Right box",(left_topleft[0]+10,left_topleft[1]-10),font,1,(20,255,255),3,cv2.LINE_AA)

    data = {}
    data['objects'] = []

    for i in range(len(scores)):
        if ((scores[i] > minimum_threshold) and (scores[i] <= 1.0)):

            x = int(((boxes[i][1]+boxes[i][3])/2)*IM_WIDTH)
            y = int(((boxes[i][0]+boxes[i][2])/2)*IM_HEIGHT)


            object_name = labels[int(classes[i])]


            ymin = int(max(1,(boxes[i][0] * imH)))
            xmin = int(max(1,(boxes[i][1] * imW)))
            ymax = int(min(imH,(boxes[i][2] * imH)))
            xmax = int(min(imW,(boxes[i][3] * imW)))


            if (xmin < left_bottomright[0]) and (xmax > right_topleft[0]):
                data['objects'].append({
                    'name': object_name,
                    'position': 'up close',
                })

            elif (xmin > left_topleft[0]) and (xmax < left_bottomright[0]):
                data['objects'].append({
                    'name': object_name,
                    'position': 'left',
                })


            elif (xmin > middle_topleft[0]) and (xmax < middle_bottomright[0]):
                data['objects'].append({
                    'name': object_name,
                    'position': 'middle',
                })

            elif (xmin > right_topleft[0]) and (xmax < right_bottomright[0]):
                data['objects'].append({
                    'name': object_name,
                    'position': 'right',
                })

            elif (xmin > left_topleft[0]) and (xmax < middle_bottomright[0]):
                data['objects'].append({
                    'name': object_name,
                    'position': 'slight left',
                })
            elif (xmin < middle_bottomright[0]) and (xmax > right_topleft[0]):
                data['objects'].append({
                    'name': object_name,
                    'position': 'slight right',
                })


            cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), (10, 255, 0), 2)

            label = '%s: %d%%' % (object_name, int(scores[i]*100)) # Example: 'person: 72%'
            labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2) # Get font size
            label_ymin = max(ymin, labelSize[1] + 10) # Make sure not to draw label too close to top of window
            cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), (255, 255, 255), cv2.FILLED) # Draw white box to put label text in
            cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text

    cv2.putText(frame,'FPS: {0:.2f}'.format(frame_rate_calc),(30,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,0),2,cv2.LINE_AA)

    fp = open("allobject.json", "w")
    json.dump(data, fp)
    fp.close()

    cv2.imshow('Object detector', frame)

    t2 = cv2.getTickCount()
    time1 = (t2-t1)/freq
    frame_rate_calc= 1/time1

    if cv2.waitKey(1) == ord('q'):
        break

cv2.destroyAllWindows()
videostream.stop()