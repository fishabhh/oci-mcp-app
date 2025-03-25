#!/usr/bin/env python3
"""
OCI MCP Server - Main Application Entry Point
"""
import logging
import os
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.router import router as api_router
from utils.config import load_config
from utils.logger import setup_logger

# Initialize the FastAPI application
app = FastAPI(
    title="OCI MCP Server",
    description="Model Context Protocol Server for Oracle Cloud Infrastructure Resource Provisioning",
    version="0.1.0",
)

# Load configuration
config_path = os.environ.get("CONFIG_PATH", "config.yaml")
if not os.path.exists(config_path):
    config_path = "config.example.yaml"
    logging.warning(f"Config file not found, using example config: {config_path}")

config = load_config(config_path)

# Setup logging
log_config = config.get("logging", {})
log_file = log_config.get("file_path", "logs/mcp_server.log")
log_level = config.get("server", {}).get("log_level", "info").upper()
setup_logger(log_file, log_level)

logger = logging.getLogger(__name__)

# Configure CORS
origins = config.get("security", {}).get("cors_origins", ["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for the MCP server"""
    return {"status": "healthy", "version": app.version}


if __name__ == "__main__":
    server_config = config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    debug = server_config.get("debug", False)
    
    logger.info(f"Starting OCI MCP Server on {host}:{port}")
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    uvicorn.run("main:app", host=host, port=port, reload=debug)
