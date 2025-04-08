import os
import firebase_admin
from firebase_admin import credentials, db
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

# 🔹 Firebase Initialization
FIREBASE_CREDENTIALS = "myaiproject-7162b-firebase-adminsdk-fbsvc-47a49c1500.json"
DATABASE_URL = "https://myaiproject-7162b-default-rtdb.firebaseio.com/"

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

# 🔹 Google Drive API Initialization
GOOGLE_DRIVE_CREDENTIALS = "mydearfellow-4a512d5e7739.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
drive_creds = Credentials.from_service_account_file(GOOGLE_DRIVE_CREDENTIALS, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=drive_creds)


# 🔹 Function to Upload Image to Google Drive
def upload_to_drive(file_path, student_id):
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext not in allowed_extensions:
        raise ValueError("❌ Invalid file format! Please use .jpg, .jpeg, or .png")

    file_metadata = {
        "name": f"{student_id}{file_ext}",
        "parents": ["11wsmN3HWxAPwHxXMvE4e43Ef5cuOpfU5"]  # Replace with your Drive folder ID
    }
    media = MediaFileUpload(file_path, mimetype=f"image/{file_ext[1:]}")
    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = file.get("id")

    # Make file publicly accessible
    drive_service.permissions().create(
        fileId=file_id, body={"role": "reader", "type": "anyone"}
    ).execute()

    # Return file link
    return f"https://drive.google.com/uc?id={file_id}"


# 🔹 Get Student Details from User
student_id = input("Enter Student ID: ")
name = input("Enter Student Name: ")
year = input("Enter Year of Study: ")
major = input("Enter Major: ")
standing = input("Enter Standing (Good/Probation): ")
starting_year = input("Enter Starting Year: ")
image_path = input("Enter path to student's image (JPG, JPEG, PNG): ")

# 🔹 Upload Image to Drive
try:
    drive_link = upload_to_drive(image_path, student_id)
    print(f"✅ Image uploaded to Drive: {drive_link}")

    # 🔹 Save Student Data to Firebase
    student_data = {
        "name": name,
        "year": year,
        "major": major,
        "standing": standing,
        "starting_year": starting_year,
        "total_attendance": 0,
        "last_attendance_time": "N/A",
        "image_url": drive_link
    }

    db.reference(f"Students/{student_id}").set(student_data)
    print(f"✅ Student {name} added to Firebase!")

except ValueError as e:
    print(e)
except Exception as e:
    print(f"❌ An error occurred: {e}")
w