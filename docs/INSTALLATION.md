# Installation Guide

## Step-by-Step Installation
1. **Clone Repository**:
   ```bash
   git clone https://github.com/fractal-core/fractal-system.git
   cd fractal-system
   ```
2. **Create Python Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: .\venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Initialize Configuration**:
   ```bash
   cp config.example.yaml config.yaml
   ```
5. **Verify Installation**:
   ```bash
   python cli.py status
   ```
