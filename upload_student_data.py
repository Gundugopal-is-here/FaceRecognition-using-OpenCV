import os
import firebase_admin
from firebase_admin import credentials, db
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# 🔹 Load Google Drive API Credentials
GDRIVE_CREDENTIALS = "mydearfellow-4a512d5e7739.json"  # Replace with your service account JSON file
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

creds = service_account.Credentials.from_service_account_file(GDRIVE_CREDENTIALS, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)

# 🔹 Load Firebase Credentials
FIREBASE_CREDENTIALS = "myaiproject-7162b-firebase-adminsdk-fbsvc-47a49c1500.json"  # Replace with your Firebase key JSON file
firebase_admin.initialize_app(credentials.Certificate(FIREBASE_CREDENTIALS), {
    "databaseURL": "https://myaiproject-7162b-default-rtdb.firebaseio.com/"  # Replace with your Firebase database URL
})

# 🔹 Google Drive Folder ID (Where images will be stored)
GDRIVE_FOLDER_ID = "11wsmN3HWxAPwHxXMvE4e43Ef5cuOpfU5"  # Replace with your actual Google Drive folder ID

# 🔹 Updated Student Data
students_data = {
    "181359": {
        "name": "Virat Kohli",
        "major": "Cricket",
        "starting_year": 2021,
        "total_attendance": 12,
        "standing": "B",
        "year": 1,
        "last_attendance_time": "2022-12-11 00:54:34"
    },
    "359912": {
        "name": "Jeff Bezos",
        "major": "Money",
        "starting_year": 2021,
        "total_attendance": 12,
        "standing": "G",
        "year": 1,
        "last_attendance_time": "2022-12-11 00:54:34"
    },
}

def find_image(student_id, folder):
    """Finds the image file with any extension for a given student ID."""
    for ext in ["jpg", "jpeg", "png"]:
        image_path = os.path.join(folder, f"{student_id}.{ext}")
        if os.path.exists(image_path):
            return image_path
    return None

def get_existing_drive_file(file_name):
    """Checks if a file already exists in Google Drive and returns its file ID if found."""
    query = f"name = '{file_name}' and '{GDRIVE_FOLDER_ID}' in parents and trashed=false"
    response = drive_service.files().list(q=query, fields="files(id)").execute()
    files = response.get("files", [])
    return files[0]["id"] if files else None

def delete_existing_drive_file(file_name):
    """Deletes an existing file in Google Drive before re-uploading."""
    file_id = get_existing_drive_file(file_name)
    if file_id:
        drive_service.files().delete(fileId=file_id).execute()
        print(f"🗑️ Deleted old file: {file_name}")

def upload_to_drive(file_path, file_name):
    """Deletes the old file, then uploads a fresh image to Google Drive & returns its public URL."""
    delete_existing_drive_file(file_name)  # Remove old file first

    file_metadata = {"name": file_name, "parents": [GDRIVE_FOLDER_ID]}
    media = MediaFileUpload(file_path, mimetype="image/jpeg")
    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    # 🔹 Make file publicly accessible
    drive_service.permissions().create(
        fileId=file["id"], body={"role": "reader", "type": "anyone"}
    ).execute()

    public_url = f"https://drive.google.com/uc?id={file['id']}"
    print(f"✅ Uploaded: {file_name} → {public_url}")
    return public_url

# 🔹 Upload Images & Save Student Data in Firebase
image_folder = "C:/Users/madha/PycharmProjects/ai_project/Images"  # Change to your image folder

for student_id, student_info in students_data.items():
    image_path = find_image(student_id, image_folder)

    if image_path:
        # 🔹 Upload to Google Drive, replacing old files
        file_name = os.path.basename(image_path)
        image_url = upload_to_drive(image_path, file_name)
    else:
        image_url = "No Image Available"

    # 🔹 Merge Image URL into Student Data
    student_info["image_url"] = image_url

    # 🔹 Save ALL Student Data + Image URL under Students/{student_id} in a SINGLE operation
    db.reference(f"Students/{student_id}").set(student_info)

print("✅ All student data and images uploaded successfully! (Duplicates Removed)")
