"""
Centralized logging configuration for EquityScanner Pro.
Uses standard logging + optional JSON output for production.
"""

import logging
import sys
from typing import Optional

def setup_logging(level: str = "INFO", json_format: bool = False) -> logging.Logger:
    """
    Configure root logger.
    In production, set json_format=True for structured logs.
    """
    logger = logging.getLogger("equityscanner")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    
    handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        # Simple JSON formatter
        import json
        from datetime import datetime
        
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "name": record.name,
                    "message": record.getMessage(),
                }
                if record.exc_info:
                    log_record["exception"] = self.formatException(record.exc_info)
                return json.dumps(log_record)
        
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
    
    logger.addHandler(handler)
    logger.propagate = False
    return logger


# Global logger instance
logger = setup_logging()
