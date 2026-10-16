import cv2
import os
import sys

student_id = sys.argv[1]

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("Camera not working")
    exit()

detector = cv2.CascadeClassifier(
    'haarcascade_frontalface_default.xml'
)

os.makedirs("dataset", exist_ok=True)

count = 0

while True:

    ret, img = cam.read()

    if not ret:
        print("Failed to capture image")
        break

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = detector.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:

        count += 1

        cv2.imwrite(
            f"dataset/User.{student_id}.{count}.jpg",
            gray[y:y+h, x:x+w]
        )

        cv2.rectangle(
            img,
            (x, y),
            (x+w, y+h),
            (255, 0, 0),
            2
        )

    cv2.imshow("Face Capture", img)

    k = cv2.waitKey(100)

    if k == 27:
        break

    elif count >= 50:
        break

cam.release()
cv2.destroyAllWindows()

print("Face Capture Completed")