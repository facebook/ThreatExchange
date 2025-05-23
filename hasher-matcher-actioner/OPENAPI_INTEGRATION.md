# OpenAPI Integration for Hasher-Matcher-Actioner (HMA)

This document explains how to use the OpenAPI 3.0 specification and documentation integration for the HMA system.

## Overview

The HMA system now includes a comprehensive OpenAPI 3.0 specification that documents all API endpoints, request/response schemas, and provides interactive documentation tools. This enables:

- **Standardized API Documentation** - Complete, machine-readable API specification
- **Interactive Testing** - Swagger UI for testing endpoints directly in the browser
- **Client SDK Generation** - Generate client libraries in multiple programming languages
- **API Validation** - Ensure API compliance and consistency
- **Integration with External Tools** - Import into Postman, Insomnia, and other API tools

## ⚠️ Critical Integration Challenges

### Dynamic Response Structure

The HMA API presents unique challenges for strongly-typed languages due to its **dynamic response structure**:

- **Hash algorithm names as object keys** (pdq, md5, sha256, etc.)
- **Keys not predictable at compile-time** - depend on runtime configuration
- **Memory allocation challenges** - cannot pre-allocate struct memory for unknown fields
- **JSON parsing limitations** - standard struct mapping fails with unknown field names

### Affected Languages & Required Workarounds

| Language | Required Type | Standard Approach Fails |
|----------|---------------|------------------------|
| **TypeScript** | `Record<string, string>` | ❌ Interface with known fields |
| **Go** | `map[string]string` | ❌ Struct with fixed fields |
| **Swift** | `[String: String]` | ❌ Codable struct with properties |
| **Rust** | `HashMap<String, String>` | ❌ Struct with known fields |
| **Java** | `Map<String, String>` | ❌ POJO with fixed properties |
| **C#** | `Dictionary<string, string>` | ❌ Class with known properties |

### API Chaining Limitation

**Direct API chaining is not supported**. Manual transformation is required:

```typescript
// ❌ This doesn't work - no direct chaining
const matches = await findMatches(await hashContent(file));

// ✅ Manual transformation required
const hashResponse = await hashContent(file);
const algorithm = Object.keys(hashResponse)[0];
const matchingInput = {
  signal: hashResponse[algorithm],
  signal_type: algorithm
};
const matches = await findMatches(matchingInput);
```

## Features

### 📚 Documentation Endpoints

The OpenAPI integration provides several documentation endpoints:

- **`/api/`** - API documentation home page with links to all tools
- **`/api/docs`** - Interactive Swagger UI for testing endpoints
- **`/api/redoc`** - Clean, responsive ReDoc documentation viewer
- **`/api/openapi.json`** - Machine-readable OpenAPI specification (JSON format)
- **`/api/openapi.yaml`** - Human-readable OpenAPI specification (YAML format)

### 🔨 Documented API Categories

The specification covers all HMA API endpoints organized by functionality:

1. **Hashing (`/h/*`)** - Content hashing operations
   - Hash content from URLs or file uploads
   - Support for photos and videos
   - **⚠️ Returns dynamic object structure**

2. **Matching (`/m/*`)** - Content matching and lookup operations
   - Raw hash lookups (**requires manual input from hashing response**)
   - Content similarity matching
   - Index status monitoring
   - Hash comparison utilities

3. **Curation (`/c/*`)** - Bank and content management operations
   - Bank creation and management
   - Content addition and removal
   - Signal exchange configuration
   - System configuration

4. **Development (`/dev/*`)** - Testing and development tools
   - Sample data seeding
   - Factory reset functionality
   - Test environment setup

## Getting Started

### 1. Start the HMA Application

Ensure your HMA application is running with the OpenAPI blueprint enabled (it's registered by default):

```bash
# Using Flask development server
flask run

# Using Gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 "OpenMediaMatch.app:create_app()"
```

### 2. Access the Documentation

Open your browser and navigate to:

- **API Home**: http://localhost:5000/api/
- **Swagger UI**: http://localhost:5000/api/docs
- **ReDoc**: http://localhost:5000/api/redoc

### 3. Download the Specification

Get the OpenAPI specification in your preferred format:

```bash
# JSON format (for tools and SDK generation)
curl http://localhost:5000/api/openapi.json > hma-api.json

# YAML format (human-readable)
curl http://localhost:5000/api/openapi.yaml > hma-api.yaml
```

## Multi-Language Integration Patterns

### TypeScript Integration

```typescript
// Type definitions for dynamic responses
type HashResponse = Record<string, string>;
type MatchingRequest = { signal: string; signal_type: string };

// Validation with Zod (limited to dynamic structure)
import { z } from 'zod';
const HashResponseSchema = z.record(z.string().min(1));

// Complete workflow with error handling
async function hashAndMatch(file: File, preferredAlgorithm?: string) {
  try {
    // 1. Hash content (returns dynamic object)
    const hashResponse: HashResponse = await hashContent(file);
    
    // 2. Validate response structure
    const validatedResponse = HashResponseSchema.parse(hashResponse);
    
    // 3. Select algorithm with fallback
    const algorithms = Object.keys(validatedResponse);
    const algorithm = preferredAlgorithm && algorithms.includes(preferredAlgorithm) 
      ? preferredAlgorithm 
      : algorithms[0];
      
    if (!algorithm) {
      throw new Error('No algorithms available in hash response');
    }
    
    // 4. Transform for matching
    const matchingRequest: MatchingRequest = {
      signal: validatedResponse[algorithm],
      signal_type: algorithm
    };
    
    // 5. Find matches
    return await findMatches(matchingRequest);
  } catch (error) {
    console.error('Hash and match workflow failed:', error);
    throw error;
  }
}
```

### Go Integration

```go
package main

import (
    "encoding/json"
    "fmt"
)

// Use map for dynamic hash response
type HashResponse map[string]string
type MatchingRequest struct {
    Signal     string `json:"signal"`
    SignalType string `json:"signal_type"`
}

func hashAndMatch(fileData []byte, preferredAlgorithm string) (interface{}, error) {
    // 1. Hash content (returns dynamic map)
    hashData, err := hashContent(fileData)
    if err != nil {
        return nil, err
    }
    
    var hashResponse HashResponse
    if err := json.Unmarshal(hashData, &hashResponse); err != nil {
        return nil, fmt.Errorf("failed to parse hash response: %w", err)
    }
    
    // 2. Select algorithm with fallback
    var algorithm string
    if _, exists := hashResponse[preferredAlgorithm]; exists {
        algorithm = preferredAlgorithm
    } else {
        // Pick first available
        for k := range hashResponse {
            algorithm = k
            break
        }
    }
    
    if algorithm == "" {
        return nil, fmt.Errorf("no algorithms available in hash response")
    }
    
    // 3. Transform for matching
    matchingRequest := MatchingRequest{
        Signal:     hashResponse[algorithm],
        SignalType: algorithm,
    }
    
    // 4. Find matches
    return findMatches(matchingRequest)
}
```

### Swift Integration

```swift
import Foundation

// Use Dictionary for dynamic hash response
typealias HashResponse = [String: String]

struct MatchingRequest: Codable {
    let signal: String
    let signalType: String
    
    enum CodingKeys: String, CodingKey {
        case signal
        case signalType = "signal_type"
    }
}

func hashAndMatch(data: Data, preferredAlgorithm: String? = nil) async throws -> Any {
    // 1. Hash content (returns dynamic dictionary)
    let hashData = try await hashContent(data)
    let hashResponse: HashResponse = try JSONDecoder().decode(HashResponse.self, from: hashData)
    
    // 2. Select algorithm with fallback
    let algorithms = Array(hashResponse.keys)
    let algorithm = preferredAlgorithm.flatMap { algorithms.contains($0) ? $0 : nil } ?? algorithms.first
    
    guard let selectedAlgorithm = algorithm,
          let hashValue = hashResponse[selectedAlgorithm] else {
        throw HMAError.noAlgorithmsAvailable
    }
    
    // 3. Transform for matching
    let matchingRequest = MatchingRequest(
        signal: hashValue,
        signalType: selectedAlgorithm
    )
    
    // 4. Find matches
    return try await findMatches(matchingRequest)
}
```

## Memory Allocation Considerations

### Compile-Time Limitations

Strongly-typed languages face these challenges:

- **Cannot determine struct size at compile time** - field names unknown
- **Memory layout unpredictable** - depends on runtime algorithm availability  
- **Fixed-size struct allocation impossible** - must use dynamic containers

### Runtime Requirements

- **Dynamic memory allocation** during JSON parsing
- **Hash map/dictionary data structures** for unknown keys
- **Heap allocation overhead** vs stack allocation for known structs
- **Runtime type checking** in some languages

### Performance Impact

```
Operation                Time Complexity    Memory Usage
Hash Map Lookup         O(1) avg, O(n) worst    Higher overhead
Direct Field Access     O(1) guaranteed          Lower overhead  
Memory Allocation       Runtime heap             vs compile-time stack
```

## Error Handling Best Practices

### Algorithm Availability Checks

```typescript
function validateAlgorithmAvailability(
  hashResponse: Record<string, string>, 
  requiredAlgorithm: string
): boolean {
  const available = Object.keys(hashResponse);
  if (available.length === 0) {
    throw new Error('No hashing algorithms available');
  }
  
  if (requiredAlgorithm && !available.includes(requiredAlgorithm)) {
    console.warn(`Requested algorithm '${requiredAlgorithm}' not available. Available: ${available.join(', ')}`);
    return false;
  }
  
  return true;
}
```

### Graceful Fallback Strategy

```typescript
function selectAlgorithmWithFallback(
  hashResponse: Record<string, string>, 
  preferenceOrder: string[] = ['pdq', 'sha256', 'md5']
): string {
  const available = Object.keys(hashResponse);
  
  // Try preferred algorithms in order
  for (const preferred of preferenceOrder) {
    if (available.includes(preferred)) {
      return preferred;
    }
  }
  
  // Fallback to first available
  if (available.length > 0) {
    console.warn(`No preferred algorithms available. Using: ${available[0]}`);
    return available[0];
  }
  
  throw new Error('No algorithms available for selection');
}
```

## SDK Generation Limitations

### Code Generator Challenges

Most OpenAPI code generators struggle with:

- **`additionalProperties` schemas** - generate overly generic types
- **Dynamic object shapes** - cannot create specific interfaces
- **Runtime type determination** - compile-time code generation limitations

### Recommended Approach

Instead of relying solely on generated SDKs:

1. **Use generated types as base** - for known structures
2. **Create custom wrappers** - for dynamic response handling
3. **Add validation layers** - for runtime type safety
4. **Document integration patterns** - for team consistency

### Custom Wrapper Example

```typescript
class HMAClientWrapper {
  constructor(private baseClient: GeneratedHMAClient) {}
  
  async hashContent(file: File): Promise<HashResponseWrapper> {
    const response = await this.baseClient.hashContent(file);
    return new HashResponseWrapper(response);
  }
  
  async findMatches(input: MatchingRequest): Promise<any> {
    return await this.baseClient.findMatches(input);
  }
}

class HashResponseWrapper {
  constructor(private data: Record<string, string>) {}
  
  getAvailableAlgorithms(): string[] {
    return Object.keys(this.data);
  }
  
  hasAlgorithm(algorithm: string): boolean {
    return algorithm in this.data;
  }
  
  getHash(algorithm: string): string | undefined {
    return this.data[algorithm];
  }
  
  toMatchingRequest(algorithm?: string): MatchingRequest {
    const selected = algorithm || this.getAvailableAlgorithms()[0];
    if (!this.hasAlgorithm(selected)) {
      throw new Error(`Algorithm ${selected} not available`);
    }
    
    return {
      signal: this.data[selected],
      signal_type: selected
    };
  }
}
```

## Role-Based Access Control

The HMA API uses role-based access control. Different endpoints require specific roles to be enabled:

- **`ROLE_HASHER`** - Required for `/h/*` endpoints (content hashing)
- **`ROLE_MATCHER`** - Required for `/m/*` endpoints (content matching)
- **`ROLE_CURATOR`** - Required for `/c/*` endpoints (content management)
- **`UI_ENABLED`** - Required for `/ui/*` endpoints (web interface)

Configure these roles in your HMA configuration file.

## API Examples

### Hash Content from URL

```bash
curl -X GET "http://localhost:5000/h/hash?url=https://example.com/image.jpg" \
  -H "accept: application/json"

# Response (dynamic structure):
# {
#   "pdq": "facd8bcb2a49bcebdec1985298d5fe84bcd006c187c598c720c3c087b3fdb318",
#   "md5": "d41d8cd98f00b204e9800998ecf8427e"
# }
```

### Manual Transformation for Matching

```bash
# Step 1: Hash content (dynamic response)
HASH_RESPONSE=$(curl -s "http://localhost:5000/h/hash?url=https://example.com/image.jpg")
echo "Hash Response: $HASH_RESPONSE"

# Step 2: Extract algorithm and hash (manual process)
ALGORITHM="pdq"  # Must choose from available keys
HASH_VALUE=$(echo $HASH_RESPONSE | jq -r ".${ALGORITHM}")

# Step 3: Use in matching API
curl -X GET "http://localhost:5000/m/raw_lookup?signal=${HASH_VALUE}&signal_type=${ALGORITHM}" \
  -H "accept: application/json"
```

### Create Content Bank and Add Content

```bash
# Create bank
curl -X POST "http://localhost:5000/c/banks" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-bank", "enabled_ratio": 1.0}'

# Add content to bank (automatic hashing + storage)
curl -X POST "http://localhost:5000/c/bank/my-bank/content?url=https://example.com/image.jpg" \
  -H "accept: application/json"
```

## Validation

The repository includes a validation script to ensure the OpenAPI specification is correct:

```bash
# Basic validation
python3 scripts/validate_openapi.py

# Include online validation (requires internet)
python3 scripts/validate_openapi.py --online
```

## Troubleshooting

### Common Issues

1. **Dynamic response parsing errors**
   - Use `Record<string, string>` or `map[string]string` types
   - Cannot use strict interfaces with known fields
   - Validate structure at runtime

2. **Algorithm not available errors**
   - Check available algorithms in response: `Object.keys(hashResponse)`
   - Implement fallback strategy for algorithm selection
   - Handle empty response gracefully

3. **Type safety violations**
   - Cannot enforce strict typing at compile time for dynamic keys
   - Use runtime validation with libraries like Zod (TypeScript)
   - Implement custom wrapper classes for type safety

4. **Memory allocation issues**
   - Use dynamic containers (maps/dictionaries) not fixed structs
   - Accept heap allocation overhead for unknown object shapes
   - Consider performance impact of hash map lookups vs direct field access

### Getting Help

- **GitHub Issues**: https://github.com/facebook/ThreatExchange/issues
- **ThreatExchange Docs**: https://developers.facebook.com/docs/threat-exchange
- **OpenAPI Specification**: https://spec.openapis.org/oas/v3.0.3/
- **Dynamic Schema Challenges**: See OpenAPI `additionalProperties` documentation

## Contributing

When contributing to the HMA API:

1. **Acknowledge dynamic response limitations** in new endpoint designs
2. **Update OpenAPI specification** for any new endpoints with dynamic behavior
3. **Test multi-language integration** patterns for breaking changes
4. **Document memory allocation impacts** for strongly-typed languages
5. **Run validation script** to ensure OpenAPI compliance
6. **Update integration patterns** in this documentation

The OpenAPI integration helps document the reality of dynamic API responses while providing clear workarounds for strongly-typed languages that need known object shapes for memory allocation and type safety. 