import pytest

# The client and fastapi_app_instance fixtures are provided by conftest.py

class TestOpenAPISchema:
    """
    Verify that the FastAPI OpenAPI schema is generated correctly and contains
    the expected information for all registered API routes.
    """

    def test_openapi_json_accessible(self, client):
        """Ensure the /openapi.json endpoint is accessible and returns a 200 OK."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()

    def test_schema_contains_expected_paths(self, client):
        """
        Verify that the expected API paths are present in the OpenAPI schema.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        schema_paths = set(schema["paths"].keys())

        # Expected paths based on src/api/app.py
        expected_paths = {
            "/invoke/naive_retriever",
            "/invoke/bm25_retriever", 
            "/invoke/contextual_compression_retriever",
            "/invoke/multi_query_retriever",
            "/invoke/ensemble_retriever",
            "/invoke/semantic_retriever",
            "/health",
            "/cache/stats",
        }

        assert expected_paths.issubset(schema_paths), f"Missing paths: {expected_paths - schema_paths}"

    def test_schema_operation_ids_are_correct(self, client):
        """
        Check that the operation IDs match the explicit operation_id parameters
        defined in the FastAPI route decorators.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        # Check a specific endpoint's operation ID
        naive_retriever_path = "/invoke/naive_retriever"
        assert naive_retriever_path in schema["paths"]
        
        post_operation = schema["paths"][naive_retriever_path].get("post")
        assert post_operation is not None, "POST operation missing for naive_retriever"
        
        # The operation_id is explicitly set in the route decorator
        assert post_operation["operationId"] == "naive_retriever"

    def test_schema_components_are_defined(self, client):
        """
        Ensure that Pydantic models used in request bodies and responses
        are correctly defined in the schema's components section.
        """
        response = client.get("/openapi.json")
        schema = response.json()
        
        assert "components" in schema
        assert "schemas" in schema["components"]
        
        # Check for the Pydantic models actually used in the API
        expected_models = ["AnswerResponse", "QuestionRequest"]
        component_schemas = schema["components"]["schemas"]
        
        for model in expected_models:
            assert model in component_schemas, f"Model '{model}' not found in schema components"
            
        # Verify the structure of key models
        question_request = component_schemas["QuestionRequest"]
        assert "question" in question_request["properties"]
        assert question_request["properties"]["question"]["type"] == "string"
        
        answer_response = component_schemas["AnswerResponse"]
        assert "answer" in answer_response["properties"]
        assert "context_document_count" in answer_response["properties"] 