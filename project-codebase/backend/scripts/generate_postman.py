import json
import os
import sys
import uuid
from typing import Dict, Any, List

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.main import app
    from fastapi.openapi.utils import get_openapi
    print("✅ Successfully imported FastAPI app")
except ImportError as e:
    print(f"❌ Failed to import app: {e}")
    print("Make sure you are running this from the backend directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during import: {e}")
    # Continue anyway if we can't import app (might be DB connection issue), 
    # but we need the schema. If main fails, we can't get schema easily.
    # Let's try to mock the DB or handle it.
    print("Attempting to proceed...")

def openapi_to_postman(openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert OpenAPI/Swagger JSON to Postman Collection v2.1."""
    
    info = openapi_schema.get("info", {})
    title = info.get("title", "FastAPI App")
    version = info.get("version", "1.0.0")
    
    postman_collection = {
        "info": {
            "name": f"{title} - v{version}",
            "description": info.get("description", "Generated from OpenAPI schema"),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "_postman_id": str(uuid.uuid4())
        },
        "item": [],
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "type": "string"
            },
            {
                "key": "token",
                "value": "",
                "type": "string"
            }
        ],
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{token}}",
                    "type": "string"
                }
            ]
        }
    }
    
    paths = openapi_schema.get("paths", {})
    tags_map = {}
    
    for path, methods in paths.items():
        for method, details in methods.items():
            tags = details.get("tags", ["default"])
            tag = tags[0] if tags else "default"
            
            if tag not in tags_map:
                tags_map[tag] = []
            
            # Format params
            url_params = []
            path_segments = path.strip("/").split("/")
            postman_path = []
            
            for segment in path_segments:
                if segment.startswith("{") and segment.endswith("}"):
                    var_name = segment[1:-1]
                    postman_path.append(f":{var_name}")
                    url_params.append({
                        "key": var_name,
                        "value": "",
                        "description": f"Path parameter: {var_name}"
                    })
                else:
                    postman_path.append(segment)
            
            # Query params
            query_params = []
            if "parameters" in details:
                for param in details["parameters"]:
                    if param.get("in") == "query":
                        query_params.append({
                            "key": param["name"],
                            "value": "",
                            "description": param.get("description", ""),
                            "disabled": False
                        })
            
            # Body
            body_props = {}
            if "requestBody" in details:
                content = details["requestBody"].get("content", {})
                if "application/json" in content:
                    schema = content["application/json"].get("schema", {})
                    ref = schema.get("$ref")
                    if ref:
                        def_name = ref.split("/")[-1]
                        # We'd need to resolve the ref to get actual fields, 
                        # but for now let's just use a placeholder
                        body_props = {"_comment": f"Load from #/components/schemas/{def_name}"}
                        
                        # Try to resolve simple schemas from components
                        if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
                            model = openapi_schema["components"]["schemas"].get(def_name)
                            if model and "properties" in model:
                                for prop_name, prop_data in model["properties"].items():
                                    example = prop_data.get("example", prop_data.get("default", ""))
                                    if prop_data.get("type") == "string" and not example:
                                        example = "string"
                                    elif prop_data.get("type") == "integer" and not example:
                                        example = 0
                                    elif prop_data.get("type") == "boolean" and not example:
                                        example = False
                                    body_props[prop_name] = example

            request_body = {
                "mode": "raw",
                "raw": json.dumps(body_props, indent=2) if body_props else "",
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            } if method not in ["get", "delete"] else None

            # Item
            item_name = details.get("summary", f"{method.upper()} {path}")
            
            item = {
                "name": item_name,
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}" + path,
                        "host": ["{{base_url}}"],
                        "path": postman_path,
                        "query": query_params,
                        "variable": url_params
                    },
                    "description": details.get("description", "")
                },
                "response": []
            }
            
            if request_body:
                item["request"]["body"] = request_body
                
            tags_map[tag].append(item)
    
    # Organize into folders
    for tag, items in tags_map.items():
        folder = {
            "name": tag.capitalize(),
            "item": items
        }
        postman_collection["item"].append(folder)
        
    return postman_collection

if __name__ == "__main__":
    try:
        print("🔍 Generating OpenAPI schema...")
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        )
        
        print("🔄 Converting to Postman collection...")
        collection = openapi_to_postman(openapi_schema)
        
        output_file = "Project_Nexus_API_Collection.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(collection, f, indent=2)
            
        print(f"✅ Successfully created Postman collection: {output_file}")
        print(f"📊 Total folders: {len(collection['item'])}")
        
    except Exception as e:
        print(f"❌ Error generating collection: {e}")
