"""
Gunicorn configuration for SISPOA backend.

Workers:      4 (recommended: 2 * CPU cores + 1)
Timeout:      120s (allows long-running report generation)
Bind:         PORT env var or default 8000
"""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = 4
timeout = 120

# Logging
accesslog = "-"
errorlog = "-"
capture_output = True
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
