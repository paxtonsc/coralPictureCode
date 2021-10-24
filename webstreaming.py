from imutils.video import VideoStream
from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import imutils
import time
import cv2
import numpy as np
import spidev 


# init output frame and a lock to ensur  thread safe 
# exchanges of the output frames.
outputFrame = None
lock = threading.Lock()


app = Flask(__name__)


vs = VideoStream(src=0).start()
time.sleep(2.0)


@app.route("/")
def index():
    return render_template("index.html")



# returns the current image stored in outputFrame as a byte array
def generate():
    global outputFrame, lock
    print("generate called")

    while True:
        with lock:
            if outputFrame is None:
                continue

            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

            if not flag:
                continue

        # frame in byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'/r/n')


# takes an image every two secounds
def get_image():
    global vs, outputFrame, lock

    while True:
        frame = vs.read()
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7,7), 0)

        with lock:
            outputFrame = frame.copy()

        time.sleep(5)


@app.route("/video_feed")
def video_feed():
    return Response(generate(),
            mimetype = "multipart/x-mixed-replace; boundary=frame")


@app.route("/send_spi")
def send_spi():
    print("sending image data via spi")

    spi = spidev.SpiDev()
    # first arg: bus, secound arg: device
    # how do we configure this
    spi.open(0,0)

    # test data for initatial fun
    data = [99, 100, 101, 102]

    for i in range(4):
        try:
            print(">>>".format(spi.xfer(data)))
            time.sleep(1)
        except(keyboardInterrupt, systemExit):
            spi.close()

    spi.close()
    print("data done transferring")
        

    return "{}"

@app.route("/send_uart")
def send_uart():
    print("sending image data via uart")
    return "{}"


if __name__=='__main__':
    
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=True,
            help="ip address of the device")
    ap.add_argument("-o", "--port", type=int, required=True,
            help="port number of server")

    args = vars(ap.parse_args())

    t = threading.Thread(target=get_image, args=())
    t.daemon = True
    t.start()


    app.run(host=args['ip'], port=args['port'], debug=True,
            threaded=True, use_reloader=False)




vs.stop()
