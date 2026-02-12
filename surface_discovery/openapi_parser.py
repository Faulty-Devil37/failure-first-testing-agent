"""OpenAPI spec parser with $ref resolution."""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import requests


@dataclass
class Parameter:
    name: str
    location: str
    param_type: Optional[str] = None
    required: bool = False
    schema: Optional[Dict[str, Any]] = None


@dataclass
class Endpoint:
    path: str
    method: str
    summary: Optional[str] = None
    parameters: List[Parameter] = None
    request_body_schema: Optional[Dict[str, Any]] = None
    operation_id: Optional[str] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []


def resolve_refs(schema: Any, spec: Dict[str, Any]) -> Any:
    """Resolve all $ref in schema recursively."""
    if not isinstance(schema, dict):
        return schema
    
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/"):
            parts = ref[2:].split("/")
            obj = spec
            for part in parts:
                obj = obj.get(part, {})
            return resolve_refs(obj, spec)
    
    result = {}
    for k, v in schema.items():
        if isinstance(v, dict):
            result[k] = resolve_refs(v, spec)
        elif isinstance(v, list):
            result[k] = [resolve_refs(item, spec) if isinstance(item, dict) else item for item in v]
        else:
            result[k] = v
    return result


def fetch_and_parse(openapi_url: str) -> List[Endpoint]:
    response = requests.get(openapi_url, timeout=10)
    response.raise_for_status()
    spec = response.json()
    
    endpoints = []
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            params = []
            for p in details.get("parameters", []):
                params.append(Parameter(
                    name=p.get("name", ""),
                    location=p.get("in", ""),
                    param_type=p.get("schema", {}).get("type"),
                    required=p.get("required", False),
                    schema=resolve_refs(p.get("schema", {}), spec)
                ))
            
            body_schema = None
            req_body = details.get("requestBody", {})
            if req_body:
                for ct, ct_spec in req_body.get("content", {}).items():
                    if "json" in ct:
                        body_schema = resolve_refs(ct_spec.get("schema", {}), spec)
                        break
            
            endpoints.append(Endpoint(
                path=path,
                method=method.lower(),
                summary=details.get("summary"),
                parameters=params,
                request_body_schema=body_schema,
                operation_id=details.get("operationId")
            ))
    
    return endpoints


def parse_from_file(file_path: str) -> List[Endpoint]:
    import yaml
    with open(file_path, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f) if file_path.endswith(('.yaml', '.yml')) else json.load(f)
    
    # For file parsing, we need to call internal parse logic
    endpoints = []
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            params = []
            for p in details.get("parameters", []):
                params.append(Parameter(
                    name=p.get("name", ""),
                    location=p.get("in", ""),
                    param_type=p.get("schema", {}).get("type"),
                    required=p.get("required", False),
                    schema=resolve_refs(p.get("schema", {}), spec)
                ))
            
            body_schema = None
            req_body = details.get("requestBody", {})
            if req_body:
                for ct, ct_spec in req_body.get("content", {}).items():
                    if "json" in ct:
                        body_schema = resolve_refs(ct_spec.get("schema", {}), spec)
                        break
            
            endpoints.append(Endpoint(
                path=path,
                method=method.lower(),
                summary=details.get("summary"),
                parameters=params,
                request_body_schema=body_schema,
                operation_id=details.get("operationId")
            ))
    
    return endpoints