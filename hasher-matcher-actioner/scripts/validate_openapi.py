#!/usr/bin/env python3
"""
Validation script for the HMA OpenAPI specification.

This script validates the OpenAPI specification for compliance with OpenAPI 3.0
standards and checks for common issues.
"""

import sys
import os
import yaml
import json
import urllib.request
import urllib.error
from pathlib import Path

def load_openapi_spec(spec_path: str) -> dict:
    """Load the OpenAPI specification from file."""
    try:
        with open(spec_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ OpenAPI spec file not found: {spec_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Invalid YAML in OpenAPI spec: {e}")
        sys.exit(1)

def validate_openapi_structure(spec: dict) -> bool:
    """Validate basic OpenAPI 3.0 structure."""
    required_fields = ['openapi', 'info', 'paths']
    missing_fields = [field for field in required_fields if field not in spec]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    # Check OpenAPI version
    if not spec['openapi'].startswith('3.0'):
        print(f"❌ Unsupported OpenAPI version: {spec['openapi']} (expected 3.0.x)")
        return False
    
    # Validate info section
    info_required = ['title', 'version']
    info_missing = [field for field in info_required if field not in spec['info']]
    if info_missing:
        print(f"❌ Missing required info fields: {info_missing}")
        return False
    
    print("✅ Basic OpenAPI structure is valid")
    return True

def validate_paths(paths: dict) -> bool:
    """Validate paths section."""
    if not paths:
        print("❌ No paths defined")
        return False
    
    issues = []
    
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            issues.append(f"Path '{path}' is not a dictionary")
            continue
            
        for method, operation in methods.items():
            if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                issues.append(f"Invalid HTTP method '{method}' in path '{path}'")
            
            # Check if operation has responses
            if 'responses' not in operation:
                issues.append(f"Missing responses for {method.upper()} {path}")
            elif not operation['responses']:
                issues.append(f"Empty responses for {method.upper()} {path}")
    
    if issues:
        print("❌ Path validation issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print(f"✅ All {len(paths)} paths are valid")
    return True

def validate_components(spec: dict) -> bool:
    """Validate components section."""
    if 'components' not in spec:
        print("⚠️  No components section defined")
        return True
    
    components = spec['components']
    issues = []
    
    # Validate schemas
    if 'schemas' in components:
        for schema_name, schema in components['schemas'].items():
            if not isinstance(schema, dict):
                issues.append(f"Schema '{schema_name}' is not a dictionary")
            elif 'type' not in schema and '$ref' not in schema and 'oneOf' not in schema and 'anyOf' not in schema and 'allOf' not in schema:
                issues.append(f"Schema '{schema_name}' missing type or reference")
    
    # Validate responses
    if 'responses' in components:
        for response_name, response in components['responses'].items():
            if not isinstance(response, dict):
                issues.append(f"Response '{response_name}' is not a dictionary")
            elif 'description' not in response:
                issues.append(f"Response '{response_name}' missing description")
    
    if issues:
        print("❌ Component validation issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    if 'schemas' in components:
        print(f"✅ Components section valid ({len(components['schemas'])} schemas)")
    else:
        print("✅ Components section valid")
    return True

def validate_external_references(spec: dict) -> bool:
    """Check for broken external references."""
    issues = []
    
    def check_refs(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                if key == '$ref' and isinstance(value, str):
                    if value.startswith('http'):
                        # External HTTP reference - could validate but might be slow
                        print(f"⚠️  External reference found: {value}")
                    elif value.startswith('#/'):
                        # Internal reference - check if it exists
                        ref_path = value[2:].split('/')
                        ref_obj = spec
                        try:
                            for part in ref_path:
                                ref_obj = ref_obj[part]
                        except (KeyError, TypeError):
                            issues.append(f"Broken internal reference: {value} (at {current_path})")
                else:
                    check_refs(value, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_refs(item, f"{path}[{i}]")
    
    check_refs(spec)
    
    if issues:
        print("❌ Reference validation issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ All references are valid")
    return True

def validate_openapi_online(spec: dict) -> bool:
    """Validate using an online OpenAPI validator (optional)."""
    try:
        # Try to use swagger.io validator
        validator_url = "https://validator.swagger.io/validator/debug"
        spec_json = json.dumps(spec).encode('utf-8')
        
        req = urllib.request.Request(
            validator_url,
            data=spec_json,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                if not result:
                    print("✅ Online validation passed")
                    return True
                else:
                    print("❌ Online validation issues:")
                    for issue in result:
                        print(f"   - {issue}")
                    return False
            else:
                print(f"⚠️  Online validator returned status {response.status}")
                return True
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception) as e:
        print(f"⚠️  Could not connect to online validator: {e}")
        return True  # Don't fail if online validation is unavailable

def main():
    """Main validation function."""
    # Find the OpenAPI spec file
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent # This is 'hasher-matcher-actioner'
    # New path to openapi.yaml within the top-level openapi/ directory
    spec_path = repo_root / "openapi" / "openapi.yaml"
    
    if not spec_path.exists():
        print(f"❌ OpenAPI spec file not found: {spec_path}")
        sys.exit(1)
    
    print(f"Validating OpenAPI spec: {spec_path}")
    spec_data = load_openapi_spec(str(spec_path))
    
    validations = [
        validate_openapi_structure(spec_data),
        validate_paths(spec_data.get('paths', {})),
        validate_components(spec_data),
        validate_external_references(spec_data)
    ]
    
    # Optional online validation (can be slow or fail due to network)
    # validations.append(validate_openapi_online(spec_data))
    
    if all(validations):
        print("\n🎉 OpenAPI specification is valid!")
        
        # Generate/update openapi.json from the validated spec_data
        # The spec_path is now, e.g., .../hasher-matcher-actioner/openapi/openapi.yaml
        # .parent will be .../hasher-matcher-actioner/openapi/
        json_spec_path = spec_path.parent / "openapi.json"
        try:
            with open(json_spec_path, 'w') as f_json:
                # Use compact separators to minimize file size, matching previous openapi.json
                json.dump(spec_data, f_json, indent=None, separators=(",", ":"))
            print(f"✅ Successfully generated/updated {json_spec_path}")
            sys.exit(0)
        except IOError as e:
            print(f"❌ Error writing openapi.json: {e}")
            sys.exit(1)
    else:
        print("\n❌ OpenAPI specification has validation errors.")
        sys.exit(1)

if __name__ == "__main__":
    main() 