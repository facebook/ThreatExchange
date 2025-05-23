# HMA OpenAPI Specification

This directory contains the OpenAPI 3.0 specification for the Hasher-Matcher-Actioner (HMA) API.

- `openapi.yaml`: The primary, human-editable source of the API specification.
- `openapi.json`: A JSON version of the specification, automatically generated from `openapi.yaml` by the `scripts/validate_openapi.py` script. This format is often preferred by tooling.

## Visualizing the Specification

You can visualize this API specification using various tools:

*   **Local IDEs:** Many code editors, like Visual Studio Code, have extensions (e.g., "OpenAPI (Swagger) Editor") that can render `openapi.yaml` or `openapi.json` and provide a Swagger UI or ReDoc-like preview.
*   **Online Editors/Viewers:**
    *   You can open/paste the content of `openapi.yaml` or `openapi.json` into [editor.swagger.io](https://editor.swagger.io).
*   **Standalone Viewers:** Tools like [ReDocly's ReDoc](https://github.com/Redocly/redoc) (e.g., using `npx redoc-cli serve openapi.yaml`) or Swagger UI can be run locally to serve the documentation.
    ```bash
    # Example using ReDoc CLI (requires Node.js/npm)
    npx redoc-cli serve openapi.yaml
    ```
    ```bash
    # Example using Swagger UI Docker image
    # Run from the 'hasher-matcher-actioner' directory:
    docker run -p 8080:8080 -e SWAGGER_JSON=/spec/openapi.json -v $(pwd)/openapi:/spec swaggerapi/swagger-ui
    ```

## Automated Rendering

A GitHub Action is planned to automatically render `openapi.yaml` into a user-friendly HTML format (e.g., using ReDoc or Swagger UI) and potentially deploy it (e.g., to GitHub Pages or S3) for easy team review. 