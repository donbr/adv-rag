# data_loader.py
import os
import requests # For downloading files
import logging # Import logging module
from langchain_community.document_loaders.csv_loader import CSVLoader
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Define the directory to store documents and the list of CSV files
DOCS_DIR = "data/raw"
CSV_FILES_BASENAMES = [
    "jw1.csv",
    "jw2.csv",
    "jw3.csv",
    "jw4.csv"
]
# Construct full paths for CSV files within the DOCS_DIR
CSV_FILES_PATHS = [os.path.join(DOCS_DIR, f) for f in CSV_FILES_BASENAMES]

BASE_URL = "https://raw.githubusercontent.com/AI-Maker-Space/DataRepository/main/"

def download_file(url, local_filename):
    logger.info(f"Attempting to download {local_filename} from {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info(f"Successfully downloaded {local_filename}.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {local_filename}: {e}")
        return False

def ensure_data_files_exist():
    """Checks if all data files exist in DOCS_DIR, downloads them if any are missing."""
    os.makedirs(DOCS_DIR, exist_ok=True) # Ensure the docs directory exists

    all_files_present = True
    for file_path in CSV_FILES_PATHS:
        if not os.path.exists(file_path):
            all_files_present = False
            logger.warning(f"File {file_path} not found.")
            break

    if not all_files_present:
        logger.info(f"One or more CSV files are missing from the '{DOCS_DIR}' directory. Attempting to download all...")
        download_success = True
        for file_basename in CSV_FILES_BASENAMES:
            file_url = BASE_URL + file_basename
            local_path = os.path.join(DOCS_DIR, file_basename)
            if not download_file(file_url, local_path):
                download_success = False
        if download_success:
            logger.info(f"All required CSV files have been downloaded to '{DOCS_DIR}'.")
        else:
            logger.error(f"Failed to download one or more CSV files. Please check the URLs and your network connection.")
            return False # Indicate failure to get files
    else:
        logger.info(f"All CSV files are present in the '{DOCS_DIR}' directory.")
    return True


def load_documents():
    if not ensure_data_files_exist():
        logger.error("Could not ensure all data files are available. Aborting document loading.")
        return [] # Return empty list if files couldn't be obtained

    documents = []
    for i, file_path in enumerate(CSV_FILES_PATHS, 1):
        # ensure_data_files_exist should have already checked this, but an extra check doesn't hurt
        if not os.path.exists(file_path):
            # This case should ideally not be reached if ensure_data_files_exist works correctly
            logger.warning(f"File {file_path} not found even after download attempt. Skipping.")
            continue

        loader = CSVLoader(
            file_path=file_path,
            metadata_columns=["Review_Date", "Review_Title", "Review_Url", "Author", "Rating"]
        )
        try:
            movie_docs = loader.load()
            for doc in movie_docs:
                # Infer movie title part from basename, e.g., jw1.csv -> John Wick 1
                movie_part = os.path.basename(file_path).replace('jw','').replace('.csv','')
                doc.metadata["Movie_Title"] = f"John Wick {movie_part}"
                doc.metadata["Rating"] = int(doc.metadata["Rating"]) if doc.metadata["Rating"] else 0
                # Assigning last_accessed_at based on movie number for demonstration
                # In a real scenario, this might be actual access time or file modification time
                doc.metadata["last_accessed_at"] = datetime.now() - timedelta(days=(len(CSV_FILES_PATHS) - int(movie_part)))
            documents.extend(movie_docs)
        except Exception as e:
            logger.error(f"Error loading or processing file {file_path}: {e}")
            continue # Skip to the next file if there's an error
    
    if not documents:
        logger.error(f"No documents were loaded. Please ensure CSV files are valid and accessible in the '{DOCS_DIR}' directory.")
    return documents

if __name__ == "__main__":
    # Logging should already be configured by importing settings or logging_config
    # If not, and this is run truly standalone, basicConfig might take over or logs might go nowhere.
    if not logging.getLogger().hasHandlers():
        from src import logging_config
        logging_config.setup_logging()
        
    logger.info("--- Running data_loader.py standalone test ---")
    loaded_docs = load_documents()
    if loaded_docs:
        logger.info(f"Successfully loaded {len(loaded_docs)} documents.")
        # Print some info from the first and last doc if available
        if len(loaded_docs) > 0:
            logger.info("Sample of first loaded document:")
            logger.info(f"  Content (first 100 chars): {loaded_docs[0].page_content[:100]}...")
            logger.info(f"  Metadata: {loaded_docs[0].metadata}")
        if len(loaded_docs) > 1:
            logger.info("Sample of last loaded document:")
            logger.info(f"  Content (first 100 chars): {loaded_docs[-1].page_content[:100]}...")
            logger.info(f"  Metadata: {loaded_docs[-1].metadata}")
    else:
        logger.warning("No documents were loaded during the standalone test.")
    logger.info("--- Finished data_loader.py standalone test ---") 