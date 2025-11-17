import cv2
import numpy as np
from multiprocessing import shared_memory
import time

# cap = cv2.VideoCapture("assets/samples/videoexample.mp4") # Adjust if necessary
cap = cv2.VideoCapture("/dev/video0") # Adjust if necessary
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

already_sharing = False 

try:
    while True:
        ret, frame = cap.read()
        if not already_sharing:
            shape = np.array(frame.shape, dtype=np.int16)
            try:
                shapeshm = shared_memory.SharedMemory(create=True, size=shape.nbytes, name="shape")
                frameshm = shared_memory.SharedMemory(create=True, size=frame.nbytes, name="frame")
                shapearr = np.ndarray(shape.shape, dtype=np.int16, buffer=shapeshm.buf)
                framearr = np.ndarray(frame.shape, dtype=frame.dtype, buffer=frameshm.buf)
            except FileExistsError:
                shapeshm = shared_memory.SharedMemory(create=False, name="shape")
                frameshm = shared_memory.SharedMemory(create=False, name="frame")
                shapearr = np.ndarray(shape.shape, dtype=np.int16, buffer=shapeshm.buf)
                framearr = np.ndarray(frame.shape, dtype=frame.dtype, buffer=frameshm.buf)
                already_sharing = True
        # Write frame and shape bytes to shared memory (not exactly efficient, but it is readable)
        # shapeshm.buf[:shape.nbytes] = shape.tobytes()
        # frameshm.buf[:frame.nbytes] = frame.tobytes()
        framearr[:] = frame
        shapearr[:] = shape
        time.sleep(1/cap.get(cv2.CAP_PROP_FPS)) # 20Hz
except KeyboardInterrupt:
    print(" Exiting...")
    cap.release()
    frameshm.unlink()
    shapeshm.unlink()
