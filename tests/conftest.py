import pytest
from fastapi.testclient import TestClient
from src.api.app import app as fastapi_app
from fastmcp import FastMCP, Client

@pytest.fixture(scope="module")
def fastapi_app_instance():
    """
    Fixture to provide an instance of the FastAPI application for testing.
    """
    return fastapi_app

@pytest.fixture(scope="module")
def client(fastapi_app_instance):
    """
    Fixture to provide a TestClient for the FastAPI application.
    This is the standard pattern for testing FastAPI applications.
    """
    with TestClient(fastapi_app_instance) as c:
        yield c

@pytest.fixture(scope="module")
def mcp_server_instance(fastapi_app_instance):
    """
    Fixture to create a real FastMCP server instance from the FastAPI app,
    for in-memory testing following the official FastMCP documentation pattern.
    """
    return FastMCP.from_fastapi(app=fastapi_app_instance)
