import cv2
import face_recognition
import pickle
import os

# Importing the student images
folderPath = "C:/Users/madha/PycharmProjects/ai_project/Images"
pathList = os.listdir(folderPath)
print("Images found:", pathList)

imgList = []
studentIds = []

# Load images and extract student IDs
for path in pathList:
    imgPath = os.path.join(folderPath, path)
    img = cv2.imread(imgPath)

    if img is not None:
        imgList.append(img)
        studentIds.append(os.path.splitext(path)[0])
    else:
        print(f"Warning: Unable to load {imgPath}")

print("Student IDs:", studentIds)


def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img)

        if encodings:  # Check if a face is detected
            encodeList.append(encodings[0])
        else:
            print("Warning: No face detected in an image. Skipping.")

    return encodeList


print("Encoding started...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, studentIds]
print("Encoding complete. Total encoded faces:", len(encodeListKnown))

# Save encodings using 'with open' to avoid file closing issues
encodeFilePath = "EncodeFile.p"
with open(encodeFilePath, 'wb') as file:
    pickle.dump(encodeListKnownWithIds, file)

print(f"Encodings saved to {encodeFilePath}")
