import cv2

faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

if faceCascade.empty():
    print("Error loading file ❌")
else:
    print("Loaded successfully ✅")