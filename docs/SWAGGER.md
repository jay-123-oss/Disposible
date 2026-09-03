# Swagger UI Integration

## Overview
The Fractal system exports standard OpenAPI 3.0.0 definitions compatible with Swagger UI, Redoc, and Postman.

## Enabling Local Swagger UI
Run the application server:
```bash
python main.py --task "Start HTTP API Gateway" --capability "integration"
```
Navigate to:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Raw OpenAPI JSON**: `http://localhost:8000/openapi.json`
- **Raw OpenAPI YAML**: `http://localhost:8000/openapi.yaml`
