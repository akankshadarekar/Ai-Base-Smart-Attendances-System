import cv2
import time

def recognize():

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trainer/trainer.yml")

    detector = cv2.CascadeClassifier(
        "haarcascade_frontalface_default.xml"
    )

    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cam.isOpened():
        print("Cannot open camera")
        return None

    # Allow camera to warm up
    for i in range(20):
        cam.read()

    recognized_id = None
    start = time.time()

    # Keep camera open for 8 seconds
    while time.time() - start < 8:

        ret, img = cam.read()

        if not ret:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces = detector.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:

            student_id, confidence = recognizer.predict(
                gray[y:y+h, x:x+w]
            )

            if confidence < 60:
                recognized_id = student_id

                cv2.rectangle(
                    img,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    img,
                    f"ID: {student_id}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

                break

        cv2.imshow("Face Login", img)

        if recognized_id is not None:
            break

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cam.release()
    cv2.destroyAllWindows()

    return recognized_id