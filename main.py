import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials, db
import time
from datetime import datetime

# 🔹 Initialize Firebase
FIREBASE_CREDENTIALS = "FIREBASE_JSON"
DATABASE_URL = "DATABASE_url"

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

# 🔹 Start Camera
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# 🔹 Load UI Assets
imgBackground = cv2.imread('Resources/background.png')
folderModePath = 'Resources/Modes'
modePath = os.listdir(folderModePath)
imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePath]

# 🔹 Load Encoded Faces
print("🔍 Loading Encode file...")
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)
encodeListKnown, studentIds = encodeListKnownWithIds
print("✅ Encode File Loaded")

# 🔹 Face Recognition Variables
modeType = 0
id = -1
studentInfo = None
student_img = None
last_detected_time = 0
last_attendance_time = 0
attendance_marked = False  # Flag to track attendance
last_face_seen_time = 0  # Time when the face was last seen


def get_student_image(student_id):
    global student_img
    student_img = None
    local_path = f"Images/{student_id}.jpg"
    if os.path.exists(local_path):
        student_img = cv2.imread(local_path)
        print(f"✅ Image loaded for ID: {student_id}")
    else:
        print(f"❌ No image found for ID: {student_id}")


while True:
    success, img = cap.read()
    if not success:
        continue

    current_time = time.time()  # Always update current_time here

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

    if faceCurFrame:
        last_face_seen_time = current_time  # Update time when face is seen

        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
            imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

            if len(faceDis) > 0:
                matchIndex = np.argmin(faceDis)
                if matches[matchIndex]:
                    new_id = studentIds[matchIndex]
                    if new_id != id or (current_time - last_detected_time) > 30:
                        id = new_id
                        studentInfo = db.reference(f"Students/{id}").get()
                        print("✅ Student Info Retrieved:", studentInfo)
                        get_student_image(id)
                        modeType = 1
                        last_detected_time = current_time
                        attendance_marked = False  # Reset attendance marking

        if studentInfo:
            # Only mark attendance if it hasn't been marked yet
            if modeType == 1 and not attendance_marked and (current_time - last_attendance_time) > 30:
                studentInfo['total_attendance'] = studentInfo.get('total_attendance', 0) + 1
                db.reference(f"Students/{id}/total_attendance").set(studentInfo['total_attendance'])
                last_attendance_time = current_time
                formatted_time = datetime.fromtimestamp(last_attendance_time).strftime('%Y-%m-%d %H:%M:%S')
                db.reference(f"Students/{id}/last_attendance_time").set(formatted_time)
                print(f"✅ Attendance Updated for {id} at {formatted_time}")
                attendance_marked = True  # Mark attendance

            # Display student information
            cv2.putText(imgBackground, str(studentInfo.get('total_attendance', 0)), (861, 125),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
            cv2.putText(imgBackground, studentInfo.get('major', 'N/A'), (1006, 550),
                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(imgBackground, str(id), (1006, 493),
                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

            if modeType != 2:
                (w, _), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                offset = (414 - w) // 2
                cv2.putText(imgBackground, studentInfo['name'], (808 + offset, 445),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 2)

            if modeType == 1 and student_img is not None:
                student_img_resized = cv2.resize(student_img, (216, 216))
                imgBackground[175:175 + 216, 909:909 + 216] = student_img_resized

        if modeType == 1 and (current_time - last_detected_time) > 5:
            modeType = 2
        if modeType == 2 and (current_time - last_detected_time) > 8:
            modeType = 3
    else:
        # If no face is detected, reset mode and attendance flag
        if (current_time - last_face_seen_time) > 20:  # Increased time to 20 seconds
            modeType = 0
            id = -1
            attendance_marked = False  # Reset flag after face disappears

    cv2.imshow("Face Attendance", imgBackground)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
