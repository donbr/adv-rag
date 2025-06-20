import pytest
import os
from unittest.mock import patch, MagicMock, call, mock_open
import requests
from langchain_core.documents import Document
from src.rag.data_loader import (
    download_file,
    ensure_data_files_exist,
    load_documents,
    DOCS_DIR,
    CSV_FILES_PATHS,
)

@patch('requests.get')
def test_download_file_success(mock_requests_get):
    """Test successful file download."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
    
    # This is the key: the context manager needs a mock for __enter__
    mock_requests_get.return_value.__enter__.return_value = mock_response
    
    # Use mock_open to mock the open call
    m_open = mock_open()
    with patch('builtins.open', m_open):
        result = download_file("http://fakeurl.com/file.csv", "local.csv")
        assert result is True
        # Verify open was called correctly
        m_open.assert_called_once_with("local.csv", 'wb')
        
        # Verify write was called with the chunks
        handle = m_open()
        assert handle.write.call_count == 2
        handle.write.assert_any_call(b'chunk1')
        handle.write.assert_any_call(b'chunk2')

@patch('requests.get', side_effect=requests.exceptions.RequestException("Test Error"))
def test_download_file_failure(mock_requests_get, caplog):
    """Test failed file download."""
    result = download_file("http://fakeurl.com/file.csv", "local.csv")
    assert result is False
    assert "Error downloading local.csv" in caplog.text

@patch('src.rag.data_loader.os.path.exists')
@patch('src.rag.data_loader.download_file', return_value=True)
def test_ensure_data_files_exist(mock_download, mock_exists):
    """Test that data files are downloaded if they don't exist."""
    mock_exists.return_value = False
    ensure_data_files_exist()
    assert mock_download.call_count == 4

@patch('src.rag.data_loader.os.path.exists', return_value=True)
def test_ensure_data_files_exist_skips_if_present(mock_exists, caplog):
    """Test that download is skipped if files exist."""
    with patch('src.rag.data_loader.download_file') as mock_download:
        result = ensure_data_files_exist()
        assert result is True
        mock_download.assert_not_called()
        assert "All CSV files are present" in caplog.text

@patch('src.rag.data_loader.ensure_data_files_exist', return_value=True)
@patch('src.rag.data_loader.CSVLoader')
def test_load_documents_success(mock_csv_loader, mock_ensure_data):
    """Test successful loading of documents from CSV files."""
    def load_side_effect(*args, **kwargs):
        return [Document(page_content="Review Content", metadata={"Rating": "5"})]
    
    mock_instance = mock_csv_loader.return_value
    mock_instance.load.side_effect = load_side_effect
    
    docs = load_documents()
    
    assert len(docs) == 4
    assert mock_csv_loader.call_count == 4
    assert docs[0].metadata["Movie_Title"] == "John Wick 1"
    assert docs[3].metadata["Movie_Title"] == "John Wick 4"
    assert docs[0].metadata["Rating"] == 5

@patch('src.rag.data_loader.ensure_data_files_exist', return_value=False)
def test_load_documents_aborts_if_data_missing(mock_ensure_data, caplog):
    """Test that document loading aborts if data files can't be ensured."""
    docs = load_documents()
    assert docs == []
    assert "Could not ensure all data files are available" in caplog.text 