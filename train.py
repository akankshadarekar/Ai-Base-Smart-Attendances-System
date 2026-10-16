import cv2
import os
import numpy as np
from PIL import Image

path = 'dataset'

recognizer = cv2.face.LBPHFaceRecognizer_create()

detector = cv2.CascadeClassifier(
    'haarcascade_frontalface_default.xml'
)

faces = []
ids = []

for imagePath in os.listdir(path):

    img_path = os.path.join(path, imagePath)

    PIL_img = Image.open(img_path).convert('L')

    img_numpy = np.array(PIL_img, 'uint8')

    id = int(imagePath.split(".")[1])

    faces_detected = detector.detectMultiScale(img_numpy)

    for (x, y, w, h) in faces_detected:
        faces.append(img_numpy[y:y+h, x:x+w])
        ids.append(id)

os.makedirs("trainer", exist_ok=True)

recognizer.train(faces, np.array(ids))

recognizer.save('trainer/trainer.yml')

print("Training Complete")