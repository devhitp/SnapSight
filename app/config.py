"""
Configuration module for SnapSight.
"""
import os

APP_NAME = "SnapSight"
APP_VERSION = "0.1.0"

ENVIRONMENT = os.getenv("SNAPSIGHT_ENV", "development")
LOG_LEVEL = os.getenv("SNAPSIGHT_LOG_LEVEL", "INFO")

# Feature Flags
FEATURE_SCREEN_CAPTURE = False
FEATURE_OCR = False
FEATURE_LOCAL_LLM = False
