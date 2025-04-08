import os
import firebase_admin
from firebase_admin import credentials, db
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

#Firebase
FIREBASE_CREDENTIALS = "FIREBASE_json"
DATABASE_URL = "DATABASE_URL"

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

#Google Drive API
GOOGLE_DRIVE_CREDENTIALS = "GDRIVE_JSON"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
drive_creds = Credentials.from_service_account_file(GOOGLE_DRIVE_CREDENTIALS, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=drive_creds)


#Upload Image to Google Drive
def upload_to_drive(file_path, student_id):
    allowed_extensions = {".jpg", ".jpeg", ".png"}
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext not in allowed_extensions:
        raise ValueError("❌ Invalid file format! Please use .jpg, .jpeg, or .png")

    file_metadata = {
        "name": f"{student_id}{file_ext}",
        "parents": ["GDRIVE_FOLDER_ID"]  # Replace with your Drive folder ID for student images
    }
    media = MediaFileUpload(file_path, mimetype=f"image/{file_ext[1:]}")
    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = file.get("id")

    drive_service.permissions().create(
        fileId=file_id, body={"role": "reader", "type": "anyone"}
    ).execute()

    #show file location
    return f"https://drive.google.com/uc?id={file_id}"


#Input details
student_id = input("Enter Student ID: ")
name = input("Enter Student Name: ")
year = input("Enter Years of Study: ")
major = input("Enter Major: ")
starting_year = input("Enter Starting Year: ")
image_path = input("Enter path to student's image (JPG, JPEG, PNG): ")  #Use Local path when uploading

#upload student image
try:
    drive_link = upload_to_drive(image_path, student_id)
    print(f"✅ Image uploaded to Drive: {drive_link}")

    #Save student data
    student_data = {
        "name": name,
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
