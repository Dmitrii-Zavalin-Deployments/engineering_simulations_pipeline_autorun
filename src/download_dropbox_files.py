import dropbox
import os
import requests
import sys

# Function to refresh the access token
def refresh_access_token(refresh_token, client_id, client_secret):
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("❌ Failed to refresh access token:", response.text)
        raise Exception("Failed to refresh access token")

# Function to delete a file from Dropbox
def delete_file_from_dropbox(dbx, file_path, log_file):
    try:
        dbx.files_delete_v2(file_path)
        log_file.write(f"Deleted file from Dropbox: {file_path}\n")
        print(f"🗑️ Deleted from Dropbox: {file_path}")
    except Exception as e:
        log_file.write(f"Failed to delete file: {file_path}, error: {e}\n")
        print(f"❌ Failed to delete {file_path}: {e}")

# Function to delete all files except .step and flow_data.json, and geometry_resolution_advice.json, and navier_stokes_runs.zip
def delete_files_except_step_and_flow(dropbox_folder, refresh_token, client_id, client_secret, log_file_path):
    access_token = refresh_access_token(refresh_token, client_id, client_secret)
    dbx = dropbox.Dropbox(access_token)

    with open(log_file_path, "a") as log_file:
        log_file.write("Starting selective deletion...\n")
        try:
            result = dbx.files_list_folder(dropbox_folder)
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    name = entry.name
                    if not (name.endswith(".step") or name == "flow_data.json" or name == "geometry_resolution_advice.json" or name == "navier_stokes_runs.zip"):
                        delete_file_from_dropbox(dbx, entry.path_lower, log_file)
            log_file.write("Selective deletion completed.\n")
        except Exception as e:
            log_file.write(f"Error during deletion: {e}\n")
            print(f"❌ Error during deletion: {e}")

# Final cleanup
def final_cleanup_function(dropbox_folder, refresh_token, client_id, client_secret, log_file_path):
    access_token = refresh_access_token(refresh_token, client_id, client_secret)
    dbx = dropbox.Dropbox(access_token)

    with open(log_file_path, "a") as log_file:
        log_file.write("Starting selective deletion...\n")
        try:
            result = dbx.files_list_folder(dropbox_folder)
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    name = entry.name
                    if not (name.endswith(".step") or name == "flow_data.json" or name == "navier_stokes_runs.zip"):
                        delete_file_from_dropbox(dbx, entry.path_lower, log_file)
            log_file.write("Selective deletion completed.\n")
        except Exception as e:
            log_file.write(f"Error during deletion: {e}\n")
            print(f"❌ Error during deletion: {e}")

# Function to download all files from Dropbox
def download_files_from_dropbox(dropbox_folder, local_folder, refresh_token, client_id, client_secret, log_file_path):
    access_token = refresh_access_token(refresh_token, client_id, client_secret)
    dbx = dropbox.Dropbox(access_token)

    with open(log_file_path, "a") as log_file:
        log_file.write("Starting download process...\n")
        try:
            os.makedirs(local_folder, exist_ok=True)

            has_more = True
            cursor = None
            while has_more:
                result = dbx.files_list_folder_continue(cursor) if cursor else dbx.files_list_folder(dropbox_folder)
                for entry in result.entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        local_path = os.path.join(local_folder, entry.name)
                        with open(local_path, "wb") as f:
                            metadata, res = dbx.files_download(path=entry.path_lower)
                            f.write(res.content)
                        log_file.write(f"Downloaded {entry.name} to {local_path}\n")
                        print(f"📥 Downloaded: {entry.name}")
                has_more = result.has_more
                cursor = result.cursor

            log_file.write("Download completed successfully.\n")
        except Exception as e:
            log_file.write(f"Error downloading files: {e}\n")
            print(f"❌ Error downloading files: {e}")

# Entry point
if __name__ == "__main__":
    mode = sys.argv[1]  # "delete" or "download"

    if mode == "delete":
        dropbox_folder = sys.argv[2]
        refresh_token = sys.argv[3]
        client_id = sys.argv[4]
        client_secret = sys.argv[5]
        log_file_path = sys.argv[6]
        delete_files_except_step_and_flow(dropbox_folder, refresh_token, client_id, client_secret, log_file_path)

    elif mode == "cleanup":
        dropbox_folder = sys.argv[2]
        refresh_token = sys.argv[3]
        client_id = sys.argv[4]
        client_secret = sys.argv[5]
        log_file_path = sys.argv[6]
        final_cleanup_function(dropbox_folder, refresh_token, client_id, client_secret, log_file_path)

    elif mode == "download":
        dropbox_folder = sys.argv[2]
        local_folder = sys.argv[3]
        refresh_token = sys.argv[4]
        client_id = sys.argv[5]
        client_secret = sys.argv[6]
        log_file_path = sys.argv[7]
        download_files_from_dropbox(dropbox_folder, local_folder, refresh_token, client_id, client_secret, log_file_path)

    else:
        print("❌ Invalid mode. Use 'delete', 'download' or 'cleanup'.")
        sys.exit(1)



