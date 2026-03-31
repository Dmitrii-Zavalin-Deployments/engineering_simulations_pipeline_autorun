# src/io/upload_to_dropbox.py

"""
Archivist I/O: Cloud Upload Module.

Compliance:
- Rule 0 (Law of Performance): Uses __slots__ to minimize memory footprint.
- Rule 8 (API Minimalism): Streamlined upload interface.
"""

import logging
from pathlib import Path

import dropbox
from dropbox.exceptions import ApiError

from src.io.dropbox_utils import TokenManager

# Standard logger setup
logger = logging.getLogger(__name__)

class CloudUploader:
    """
    Handles secure uploading of simulation artifacts.
    Uses __slots__ per Rule 0 to minimize memory footprint.
    """
    __slots__ = ['dbx']

    def __init__(self, token_manager: TokenManager, refresh_token: str):
        logger.debug("Initializing CloudUploader and refreshing access token...")
        access_token = token_manager.refresh_access_token(refresh_token)
        self.dbx = dropbox.Dropbox(access_token)

    def upload(self, local_path: Path, dropbox_folder: str):
        """
        Atomic upload operation with explicit path handling.
        """
        if not local_path.exists():
            error_msg = f"Local file '{local_path}' not found."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Ensure dropbox_folder starts with a slash and does not end with one
        folder = f"/{dropbox_folder.strip('/')}"
        dropbox_file_path = f"{folder}/{local_path.name}"
        
        logger.info(f"Uploading {local_path.name} to {folder}...")

        try:
            with open(local_path, "rb") as f:
                # Rule 0: Using f.read() is fine for small/medium Zips, 
                # for multi-GB files, we would use session_upload.
                self.dbx.files_upload(
                    f.read(), 
                    dropbox_file_path, 
                    mode=dropbox.files.WriteMode.overwrite
                )
            
            logger.info(f"✅ Successfully uploaded: {dropbox_file_path}")
            
        except ApiError as e:
            logger.error(f"❌ Dropbox API error during upload: {str(e)}")
            raise
        except Exception as e:
            logger.critical(f"Unexpected error during upload: {str(e)}")
            raise