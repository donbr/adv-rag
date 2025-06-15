#!/usr/bin/env python3
"""
Export FastMCP server definitions to shareable JSON format.
"""
import json
import asyncio
import sys
import os
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback
    except ImportError:
        import toml as tomllib  # Final fallback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get project root using git or fallback to current directory resolution."""
    try:
        # Try git first (most reliable)
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5, check=True
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        # Fallback to relative path resolution
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent  # Go up from scripts/mcp/ to project root
        logger.warning(f"Git not available, using fallback project root: {project_root}")
        return project_root

# Add project root to Python path
project_root = get_project_root()
sys.path.insert(0, str(project_root))

try:
    from fastmcp import Client
    from src.mcp_server.fastapi_wrapper import mcp
    from src.main_api import app as fastapi_app
except ImportError as e:
    logger.error(f"Failed to import MCP components: {e}")
    logger.error("Ensure you're running from the project root and dependencies are installed")
    sys.exit(1)

# Add imports for enhanced MCP features
import tomllib
from typing import List, Dict, Any, Optional, Tuple
import subprocess
import logging

async def export_mcp_definitions():
    """Export MCP server definitions as JSON."""
    
    # Extract real metadata from the project
    project_meta, fastapi_meta, mcp_meta = extract_project_metadata()
    config = load_mcp_config()

    #async with Client(mcp) as client:
    async with Client(
        "http://127.0.0.1:8001/mcp/"
    ) as client:

        # Get all definitions
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        
        # Build the standard schema format (legacy/community format)
        schema = {
            "_note": "This is a LEGACY/COMMUNITY format. Use mcp_server_official.json for production.",
            "_extracted_metadata": {
                "project_meta": project_meta,
                "fastapi_meta": fastapi_meta,
                "mcp_meta": mcp_meta
            },
            "server_info": {
                "name": mcp_meta.get("name", project_meta.get("name", "advanced-rag")),
                "description": fastapi_meta.get("description") or project_meta.get("description", "FastAPI Integration"),
                "repo_url": "https://github.com/donbr/advanced-rag",  # repo-specific
                "server_type": "FastAPI Integration",
                "server_category": ["RAG", "Search", "AI", "LangChain"],
                "server_version": fastapi_meta.get("version", project_meta.get("version", "0.1.0"))
            },
            "tools": [],
            "resources": [],
            "prompts": []
        }
        
        # Convert tools with clean descriptions (legacy format uses snake_case)
        for tool in tools:
            # Clean up the description - remove FastAPI response documentation
            clean_description = tool.description.split('\n\n\n**Responses:**')[0] if '\n\n\n**Responses:**' in tool.description else tool.description
            
            tool_def = {
                "name": tool.name,
                "description": clean_description,
                "input_schema": tool.inputSchema  # Legacy format uses snake_case
            }
            
            # Add response info as a note (not part of MCP spec, but useful for documentation)
            if hasattr(tool, 'annotations'):
                tool_def["annotations"] = tool.annotations
                
            schema["tools"].append(tool_def)
        
        # Convert resources  
        for resource in resources:
            schema["resources"].append({
                "name": resource.name,
                "description": resource.description,
                "uri": resource.uri
            })
            
        # Convert prompts
        for prompt in prompts:
            schema["prompts"].append({
                "name": prompt.name,
                "description": prompt.description,
                "template": getattr(prompt, 'template', None)
            })
        
        return schema

def extract_project_metadata():
    """Extract metadata from pyproject.toml, FastAPI app, and MCP server."""
    
    # Load MCP configuration
    config = load_mcp_config()
    
    # Extract git repository information for dynamic URLs
    repo_info = extract_git_repo_info()
    
    # Try to load project metadata from pyproject.toml
    project_meta = {}
    pyproject_path = project_root / "pyproject.toml"
    
    if pyproject_path.exists():
        try:
            # Always use binary mode for tomllib/tomli
            with open(pyproject_path, 'rb') as f:
                pyproject_data = tomllib.load(f)
            project_meta = pyproject_data.get("project", {})
            logger.info(f"Successfully loaded project metadata from {pyproject_path}")
        except Exception as e:
            # Fallback to text mode for toml library
            try:
                with open(pyproject_path, 'r', encoding='utf-8') as f:
                    pyproject_data = tomllib.load(f)
                project_meta = pyproject_data.get("project", {})
                logger.info(f"Successfully loaded project metadata using fallback method")
            except Exception as e2:
                logger.warning(f"Could not parse pyproject.toml: {e2}")
                project_meta = {}
    else:
        logger.warning(f"pyproject.toml not found at {pyproject_path}")
    
    # Extract FastAPI app metadata
    fastapi_meta = {
        "title": getattr(fastapi_app, "title", "Unknown FastAPI App"),
        "description": getattr(fastapi_app, "description", ""),
        "version": getattr(fastapi_app, "version", "0.0.0")
    }
    
    # Try to get MCP server info from the mcp instance
    mcp_meta = {}
    try:
        if hasattr(mcp, 'server_info'):
            mcp_meta = mcp.server_info
        elif hasattr(mcp, 'name'):
            mcp_meta["name"] = mcp.name
    except Exception as e:
        logger.warning(f"Could not extract MCP server metadata: {e}")
    
    return project_meta, fastapi_meta, mcp_meta

def load_mcp_config():
    """Load MCP configuration from mcp_config_http.toml."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            try:
                import toml as tomllib
            except ImportError:
                logger.warning("No TOML library available. Using defaults.")
                return {}
    
    config_path = Path(__file__).parent / "mcp_config_http.toml"
    if not config_path.exists():
        logger.warning(f"mcp_config_http.toml not found at {config_path}. Using defaults.")
        return {}
    
    try:
        with open(config_path, 'rb') as f:
            config = tomllib.load(f)
            logger.info(f"Successfully loaded MCP configuration from {config_path}")
            return config
    except Exception as e:
        logger.warning(f"Could not load mcp_config_http.toml: {e}")
        return {}

def extract_git_repo_info():
    """Extract git repository information for dynamic URL generation."""
    try:
        # Get remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5, check=True
        )
        
        remote_url = result.stdout.strip()
        
        # Parse GitHub URLs
        if "github.com" in remote_url:
            # Handle both HTTPS and SSH formats
            if remote_url.startswith("git@"):
                # git@github.com:owner/repo.git -> owner/repo
                repo_path = remote_url.split(":")[-1].replace(".git", "")
            else:
                # https://github.com/owner/repo.git -> owner/repo
                repo_path = remote_url.split("github.com/")[-1].replace(".git", "")
            
            owner, repo = repo_path.split("/")
            repo_info = {"owner": owner, "repo": repo, "full_name": repo_path}
            logger.info(f"Successfully extracted git repository info: {repo_info['full_name']}")
            return repo_info
        
        logger.warning("Repository is not hosted on GitHub")
        return {}
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"Could not extract git repository information: {e}")
        return {}
    except Exception as e:
        logger.warning(f"Unexpected error extracting git info: {e}")
        return {}

async def export_mcp_definitions_official():
    """Export MCP server definitions using official MCP protocol format."""
    
    # Extract real metadata from the project
    project_meta, fastapi_meta, mcp_meta = extract_project_metadata()
    config = load_mcp_config()
    repo_info = extract_git_repo_info()
    
    # Dynamic URL generation
    repo_full_name = repo_info.get("full_name", f"{config.get('metadata', {}).get('repo_owner', 'unknown')}/{config.get('metadata', {}).get('repo_name', 'unknown')}")
    
    async with Client(mcp) as client:
        # Get all definitions using the official MCP protocol
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()
        
        # Build official MCP server descriptor using real metadata and config
        server_descriptor = {
            "$schema": config.get("server", {}).get("schema_url", "https://raw.githubusercontent.com/modelcontextprotocol/specification/main/schema/server.json"),
            "$id": config.get("server", {}).get("id_template", "https://github.com/{repo}/mcp-server.json").format(repo=repo_full_name),
            "name": mcp_meta.get("name", project_meta.get("name", "advanced-rag")),
            "version": fastapi_meta.get("version", project_meta.get("version", "0.1.0")),
            "description": fastapi_meta.get("description") or project_meta.get("description", config.get("metadata", {}).get("default_description", "FastAPI to MCP Integration")),
            "repository": {
                "type": "git",
                "url": config.get("server", {}).get("repository_url_template", "https://github.com/{repo}.git").format(repo=repo_full_name)
            },
            "categories": config.get("server", {}).get("categories", ["RAG", "Search", "AI", "LangChain"]),
            "keywords": config.get("server", {}).get("keywords", ["rag", "retrieval", "langchain", "fastapi"]),
            "capabilities": config.get("capabilities", {
                "tools": {"listChanged": False},
                "resources": {"subscribe": False, "listChanged": False},
                "prompts": {"listChanged": False},
                "logging": {}
            }),
            "protocolVersion": config.get("server", {}).get("protocol_version", "2024-11-05"),
            "tools": [],
            "resources": [],
            "prompts": []
        }
        
        # Add optional fields if available in project metadata or config
        license_info = project_meta.get("license") or config.get("metadata", {}).get("default_license")
        if license_info:
            # Handle both string and dict license formats
            if isinstance(license_info, dict) and "text" in license_info:
                server_descriptor["license"] = license_info["text"]
            else:
                server_descriptor["license"] = str(license_info)
        
        # Extract author information
        author_info = None
        if "authors" in project_meta and project_meta["authors"]:
            # Extract author from pyproject.toml format
            author_data = project_meta["authors"][0]
            if isinstance(author_data, dict) and "name" in author_data:
                author_info = author_data["name"]
            else:
                author_info = str(author_data)
        elif config.get("metadata", {}).get("default_author"):
            author_info = config.get("metadata", {}).get("default_author")
        
        if author_info:
            server_descriptor["author"] = author_info
        
        if "homepage" in project_meta:
            server_descriptor["homepage"] = project_meta["homepage"]
        
        # Convert tools to official format (using camelCase)
        for tool in tools:
            # Clean description - remove FastAPI response documentation
            clean_description = tool.description.split('\n\n\n**Responses:**')[0] if '\n\n\n**Responses:**' in tool.description else tool.description
            
            tool_def = {
                "name": tool.name,
                "description": clean_description,
                "inputSchema": tool.inputSchema  # camelCase as per spec
            }
            
            # Add modern MCP annotations for governance and UX
            annotations = generate_enhanced_tool_annotations(tool.name, config)
            tool_def["annotations"] = annotations
            
            # Add practical examples for better LLM understanding
            examples = generate_enhanced_examples(tool.name, config)
            tool_def["examples"] = examples
            
            server_descriptor["tools"].append(tool_def)
        
        # Convert resources
        for resource in resources:
            server_descriptor["resources"].append({
                "name": resource.name,
                "description": resource.description,
                "uri": resource.uri,
                "mimeType": getattr(resource, 'mimeType', 'application/json')
            })
            
        # Convert prompts
        for prompt in prompts:
            prompt_def = {
                "name": prompt.name,
                "description": prompt.description
            }
            
            # Add arguments if available
            if hasattr(prompt, 'arguments') and prompt.arguments:
                prompt_def["arguments"] = prompt.arguments
                
            server_descriptor["prompts"].append(prompt_def)
        
        return server_descriptor

def generate_enhanced_tool_annotations(tool_name: str, config: dict) -> dict:
    """Generate comprehensive tool annotations based on MCP 2025-03-26 specification."""
    base_annotations = config.get("annotations", {}).get("default", {})
    governance = config.get("annotations", {}).get("governance", {})
    resources = config.get("annotations", {}).get("resources", {})
    
    # Tool-specific overrides
    overrides = config.get("annotations", {}).get("overrides", {}).get(tool_name, {})
    
    # Enhanced annotations for MCP 2025-03-26
    annotations = {
        "audience": base_annotations.get("audience", ["human", "llm"]),
        "cachePolicy": {
            "ttl": base_annotations.get("cache_ttl_seconds", 300)
        },
        "governance": {
            "dataAccess": governance.get("data_access", "public"),
            "aiEnabled": governance.get("ai_enabled", True),
            "category": governance.get("category", "search"),
            "requiresApproval": governance.get("requires_approval", False),
            # NEW: Enhanced security annotations for 2025-03-26
            "isReadOnly": tool_name not in ["upload", "delete", "modify"],  # Most RAG tools are read-only
            "isDestructive": False,  # RAG retrieval tools are non-destructive
            "hasNetworkAccess": True,  # Vector database access
            "dataClassification": "public"  # Movie review data is public
        },
        "resources": {
            "isIntensive": overrides.get("is_intensive", resources.get("is_intensive", False)),
            "estimatedDuration": resources.get("estimated_duration", "medium"),
            # NEW: Resource usage annotations
            "memoryUsage": "medium" if "ensemble" in tool_name else "low",
            "networkUsage": "medium",  # Vector database queries
            "storageAccess": "read"    # Read-only access to vector stores
        },
        # NEW: Trust and safety annotations
        "trustAndSafety": {
            "contentFiltering": True,   # Filter inappropriate content
            "rateLimited": True,        # Implement rate limiting
            "auditLogged": True,        # Log all tool usage
            "requiresHumanInLoop": False  # RAG searches don't need human approval
        }
    }
    
    # Apply tool-specific resource intensity overrides
    if tool_name in ["ensemble_retriever", "contextual_compression_retriever", "multi_query_retriever"]:
        annotations["resources"]["isIntensive"] = True
        annotations["resources"]["memoryUsage"] = "high"
        annotations["trustAndSafety"]["rateLimited"] = True
        annotations["cachePolicy"]["ttl"] = 600  # Longer cache for intensive operations
    
    return annotations

def generate_enhanced_examples(tool_name: str, config: dict) -> List[dict]:
    """Generate enhanced examples with proper content types for MCP 2025-03-26."""
    questions = config.get("examples", {}).get("default_questions", [
        "What makes a good action movie?",
        "How does John Wick compare to other action heroes?"
    ])
    
    examples = []
    for i, question in enumerate(questions[:2]):  # Limit to 2 examples per tool
        example = {
            "id": f"{tool_name}_example_{i+1}",
            "description": f"Example {tool_name.replace('_', ' ')} search for: {question}",
            "input": {
                "question": question
            },
            "output": {
                # NEW: Support for multiple content types in 2025-03-26
                "contentTypes": ["text"],  # RAG tools primarily return text
                "schema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "enum": ["text"]},
                                    "text": {"type": "string"}
                                }
                            }
                        },
                        "isError": {"type": "boolean"}
                    }
                },
                "description": f"Returns relevant movie review excerpts about {question.lower()}"
            }
        }
        examples.append(example)
    
    return examples

def validate_against_official_schema(server_descriptor: dict) -> Tuple[bool, str]:
    """Validate the generated schema against the official MCP JSON schema."""
    try:
        import jsonschema
        import requests
        
        schema_url = server_descriptor.get("$schema")
        if not schema_url:
            return False, "No $schema URL found in server descriptor"
        
        logger.info(f"Fetching official schema for validation: {schema_url}")
        
        try:
            response = requests.get(schema_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            return False, f"Could not fetch official schema: {e}"
        
        try:
            official_schema = response.json()
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in official schema: {e}"
        
        # Validate our schema against the official one
        try:
            jsonschema.validate(server_descriptor, official_schema)
            return True, "Schema validation passed"
        except jsonschema.ValidationError as e:
            return False, f"Schema validation failed: {e.message}"
        except jsonschema.SchemaError as e:
            return False, f"Official schema is invalid: {e.message}"
            
    except ImportError:
        logger.warning("jsonschema library not available. Install with: pip install jsonschema")
        return False, "jsonschema library not installed"
    except Exception as e:
        return False, f"Unexpected validation error: {str(e)}"

async def main():
    """Export and save MCP definitions."""
    logger.info("🔄 Exporting MCP server definitions...")
    
    try:
        # Export community format
        community_schema = await export_mcp_definitions()
        
        # Export official MCP format
        official_schema = await export_mcp_definitions_official()
        
        # Strict JSON-Schema validation
        if official_schema.get("$schema"):
            logger.info("🔍 Performing strict JSON-Schema validation...")
            is_valid, validation_message = validate_against_official_schema(official_schema)
            if is_valid:
                logger.info("✅ Schema validation passed!")
            else:
                logger.error(f"❌ Schema validation failed: {validation_message}")
                logger.warning("Generated schema may not be fully compliant with MCP specification")
        
        # Save community format
        community_file = Path("mcp_server_schema.json")
        with open(community_file, 'w', encoding='utf-8') as f:
            json.dump(community_schema, f, indent=2, ensure_ascii=False)
        
        # Save official format
        official_file = Path("mcp_server_official.json")
        with open(official_file, 'w', encoding='utf-8') as f:
            json.dump(official_schema, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(official_schema['tools'])} tools, {len(official_schema['resources'])} resources, {len(official_schema['prompts'])} prompts")
        print(f"📄 Legacy/Community format: {community_file.absolute()}")
        print(f"📄 🎯 Official MCP format (RECOMMENDED): {official_file.absolute()}")
        
        # Show extracted metadata
        print(f"\n📊 Extracted Metadata:")
        project_meta, fastapi_meta, mcp_meta = extract_project_metadata()
        print(f"  • Project name: {project_meta.get('name', 'N/A')} (from pyproject.toml)")
        print(f"  • Project version: {project_meta.get('version', 'N/A')} (from pyproject.toml)")
        print(f"  • FastAPI title: {fastapi_meta.get('title', 'N/A')} (from FastAPI app)")
        print(f"  • FastAPI description: {fastapi_meta.get('description', 'N/A')[:50]}... (from FastAPI app)")
        print(f"  • FastAPI version: {fastapi_meta.get('version', 'N/A')} (from FastAPI app)")
        print(f"  • MCP metadata: {mcp_meta if mcp_meta else 'None found'}")
        
        # Print tool summary
        print(f"\n🛠️ Available Tools:")
        for tool in official_schema['tools']:
            print(f"  • {tool['name']}: {tool['description']}")
        
        # Validate that we have complete tool definitions using official format
        print(f"\n🔍 Official MCP Schema Validation:")
        for tool in official_schema['tools']:
            has_schema = tool.get('inputSchema') is not None  # Official format uses camelCase
            has_properties = bool(tool.get('inputSchema', {}).get('properties', {}))
            has_required = bool(tool.get('inputSchema', {}).get('required', []))
            print(f"  • {tool['name']}: Schema✅ Properties✅ Required✅" if has_schema and has_properties and has_required else f"  • {tool['name']}: Issues detected")
        
        # Schema compliance check
        print(f"\n🎯 Official MCP Schema Compliance:")
        print(f"  • $schema field: {'✅' if official_schema.get('$schema') else '❌'}")
        print(f"  • $id field: {'✅' if official_schema.get('$id') else '❌'}")
        print(f"  • camelCase inputSchema: {'✅' if all(tool.get('inputSchema') for tool in official_schema['tools']) else '❌'}")
        print(f"  • Capabilities defined: {'✅' if official_schema.get('capabilities') else '❌'}")
        print(f"  • Protocol version: {'✅' if official_schema.get('protocolVersion') else '❌'}")
        print(f"  • License field: {'✅' if official_schema.get('license') else '❌'}")
        print(f"  • Author field: {'✅' if official_schema.get('author') else '❌'}")
        
        print(f"\n💡 MCP Specification Notes:")
        print(f"   • Official schema: {official_schema.get('$schema', 'N/A')}")
        print(f"   • Tool inputs use 'inputSchema' (camelCase), not 'input_schema'")
        print(f"   • Tool responses are defined by MCP protocol content types: text, image, audio, resource")
        print(f"   • Use the Official MCP format for production deployments")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 