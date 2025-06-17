from setuptools import setup, find_packages

setup(
    name="shipra-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "python-dotenv==1.0.0",
        "openai==1.3.0",
        "httpx==0.25.1",
        "pydantic==2.4.2",
        "python-multipart==0.0.6",
        "loguru==0.7.2",
        "typing-extensions>=4.7.1",
        "structlog==23.2.0",
        "tenacity==8.2.3",
        "pydantic-settings==2.1.0",
    ],
    python_requires=">=3.11",
) 