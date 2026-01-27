t whic# Installation Guide for Python 3.13.9

## Prerequisites

### Python Version Support

#### Supabase Python Client
- **Supported Python Versions**: 3.8 - 3.13
- **Current Version**: 2.27.2
- **Dependencies**: httpx>=0.26,<0.29, yarl>=1.22.0

#### Snowflake Connector for Python  
- **Supported Python Versions**: 3.9 - 3.13
- **Current Version**: 3.18.0
- **Dependencies**: cryptography>=3.1.0, requests<3.0.0, pyOpenSSL>=22.0.0

#### Snowflake Snowpark for Python
- **Supported Python Versions**: 3.9 - 3.13  
- **Current Version**: 1.44.0
- **Dependencies**: snowflake-connector-python, cloudpickle, protobuf

### ✅ **Python 3.13.9 Compatibility**
Both Supabase and Snowflake packages officially support Python 3.13, so your current Python version is fully compatible!

### Windows Users
For Windows users, you may need to install Microsoft Visual C++ Build Tools:
1. Download and install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Or install [Visual Studio Community](https://visualstudio.microsoft.com/vs/community/) with C++ build tools

### Alternative: Use Pre-compiled Binaries

If you encounter psycopg2 compilation issues, use the pre-compiled binary:

```bash
# Install psycopg2-binary (pre-compiled, no PostgreSQL headers needed)
pip install psycopg2-binary
```

## Installation Steps

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Upgrade pip
```bash
pip install --upgrade pip
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Alternative Installation (if issues occur)

If you encounter dependency conflicts, install packages individually:

```bash
# Core dependencies
pip install fastapi uvicorn[standard] sqlalchemy pydantic pydantic-settings

# Database
pip install psycopg2-binary

# Authentication
pip install python-multipart passlib[bcrypt] python-jose[cryptography]

# HTTP & WebSockets
pip install httpx websockets==11.0.2

# Storage
pip install supabase

# Environment
pip install python-dotenv

# AI
pip install openai google-generativeai

# Snowflake
pip install snowflake-connector-python snowflake-snowpark-python
```

## Common Issues & Solutions

### Issue 1: psycopg2 compilation error
```
Error: pg_config executable not found.
```

**Solution**: Use psycopg2-binary instead of psycopg2
```bash
pip uninstall psycopg2
pip install psycopg2-binary
```

### Issue 2: websockets.asyncio module not found
```
ModuleNotFoundError: No module named 'websockets.asyncio'
```

**Solution**: Install compatible websockets version
```bash
pip install websockets==11.0.2
```

### Issue 3: Dependency conflicts
```
ERROR: Cannot install package==X because package==Y is already installed
```

**Solution**: Use pip-tools or install specific versions
```bash
pip install --force-reinstall package==specific_version
```

## Verification

After installation, verify all packages are working:

```python
# Test imports
import fastapi
import uvicorn
import sqlalchemy
import psycopg2
import websockets
import supabase
import openai
import snowflake.connector

print("All packages imported successfully!")
```

## Running the Application

```bash
# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The application should now be running at `http://localhost:8000`