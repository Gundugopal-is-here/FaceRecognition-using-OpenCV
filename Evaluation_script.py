import cv2
import face_recognition
import pickle
import time
import csv
import os

# Load the encoded faces from the pickle file
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)

encodeListKnown, studentIds = encodeListKnownWithIds

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Width
cap.set(4, 480)  # Height

# Create or open the CSV file for logging test results
csv_file = "test_results.csv"
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Student ID", "Match Status", "Processing Time (s)", "Condition"])

def test_face_recognition():
    print("🔍 Starting face recognition evaluation... Press 'q' to exit.")

    while True:
        success, img = cap.read()
        if not success:
            print("❌ Camera error!")
            break

        start_time = time.time()  # Start time for processing

        # Convert image to RGB and resize
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        # Detect faces and get encodings
        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        # Process each detected face
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

            if len(faceDis) > 0:
                matchIndex = int(faceDis.argmin())  # Get best match index

                if matches[matchIndex]:  # If a match is found
                    student_id = studentIds[matchIndex]
                    match_status = "Match Found"
                else:
                    student_id = "Unknown"
                    match_status = "No Match"

                end_time = time.time()  # End time for processing
                processing_time = round(end_time - start_time, 4)

                # Save results to CSV
                with open(csv_file, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([student_id, match_status, processing_time, "Normal Condition"])

                print(f"✅ {match_status} - Student ID: {student_id} - Time: {processing_time} sec")

        # Display camera feed
        cv2.imshow("Face Recognition Test", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("✅ Evaluation complete! Results saved in test_results.csv.")

# Run the evaluation
test_face_recognition()
