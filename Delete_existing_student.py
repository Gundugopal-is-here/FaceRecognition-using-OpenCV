import firebase_admin
from firebase_admin import credentials, db
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# 🔹 Firebase Initialization
FIREBASE_CREDENTIALS = "firebase.json"
DATABASE_URL = "firebase_database_URL"

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

# 🔹 Google Drive API Initialization
GOOGLE_DRIVE_CREDENTIALS = "GDRIVE_API_JSON"
SCOPES = ["https://www.googleapis.com/auth/drive"]
drive_creds = Credentials.from_service_account_file(GOOGLE_DRIVE_CREDENTIALS, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=drive_creds)


# 🔹 Function to find and delete the student image in Google Drive
def delete_student_image(student_id):
    query = f"name contains '{student_id}' and trashed=false"
    response = drive_service.files().list(q=query, fields="files(id)").execute()
    files = response.get("files", [])

    if files:
        for file in files:
            drive_service.files().delete(fileId=file["id"]).execute()
            print(f"🗑️ Deleted image from Google Drive for Student ID: {student_id}")
    else:
        print(f"⚠️ No image found in Google Drive for Student ID: {student_id}")


# 🔹 Function to delete student from Firebase and Google Drive
def delete_student(student_id):
    student_ref = db.reference(f"Students/{student_id}")

    # Check if student exists
    if student_ref.get() is not None:
        # Delete student image from Google Drive
        delete_student_image(student_id)

        # Delete student record from Firebase
        student_ref.delete()
        print(f"✅ Student {student_id} deleted successfully from Firebase and Google Drive.")
    else:
        print(f"⚠️ Student ID {student_id} not found in Firebase.")


# 🔹 Get Student ID from User & Delete
student_id = input("Enter Student ID to delete: ")
delete_student(student_id)
