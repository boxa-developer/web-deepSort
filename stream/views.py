from django.http import StreamingHttpResponse
from django.views.decorators import gzip
import numpy as np
import threading
import cv2
from django.conf import settings
import os


class VideoCamera(object):
    def __init__(self):
        url = 'rtsp://admin:parol12345@192.168.4.220:554/cam/realmonitor?channel=1&subtype=0'
        self.video = cv2.VideoCapture(url)
        (self.grabbed, self.frame) = self.video.read()
        threading.Thread(target=self.update, args=()).start()
        self.haar = cv2.CascadeClassifier(os.path.join(settings.MEDIA_ROOT, 'cars.xml'))

    def __del__(self):
        self.video.release()

    ########################################################################
    # All detections and Tracking Happens Here!
    def detect_car(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        cars = self.haar.detectMultiScale(gray, 1.1, 1)
        for (x, y, w, h) in cars:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
        return image
    #
    ########################################################################
    def get_frame(self):
        image = self.frame
        image = self.detect_car(image)
        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def update(self):
        while True:
            (self.grabbed, self.frame) = self.video.read()


cam = VideoCamera()


def gen(camera):
    while True:
        frame = cam.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@gzip.gzip_page
def live(request):
    try:
        return StreamingHttpResponse(gen(VideoCamera()), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        pass
