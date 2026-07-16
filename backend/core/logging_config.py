"""
ProcureAI - File Summary

What it does:
Configures advanced logging using structlog, rotating files, and GCP JSON logging styles.

What it means:
System-wide log formatter and third-party logging hijacker (Uvicorn, FastAPI, SQL session logging).

Importance in Project:
Medium. Crucial for production debugging, system telemetry, and pipeline auditing.
"""

import logging
import os
import sys
import structlog

def setup_logging(log_level: str = "INFO", log_format: str = "CONSOLE"):
    """
    Configures structlog to work with python's standard logging library.
    Ensures that standard library logs (like uvicorn, fastapi, sqlalchemy)
    are routed through structlog and formatted accordingly.
    """
    # Map log level string to numeric constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Processors shared between structlog and standard logging
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    def clean_stdlib_keys(logger, method_name, event_dict):
        """Clean up internal keys added by structlog's standard library integration."""
        event_dict.pop("_record", None)
        event_dict.pop("_from_structlog", None)
        return event_dict

    if log_format.upper() == "JSON":
        def add_gcp_severity(logger, method_name, event_dict):
            """Map level to severity for GCP Cloud Logging."""
            if "level" in event_dict:
                event_dict["severity"] = event_dict["level"].upper()
            return event_dict

        processors = shared_processors + [
            add_gcp_severity,
            clean_stdlib_keys,
            structlog.processors.JSONRenderer()
        ]
        
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                add_gcp_severity,
                clean_stdlib_keys,
                structlog.processors.JSONRenderer()
            ]
        )
    else:
        processors = shared_processors + [
            clean_stdlib_keys,
            structlog.dev.ConsoleRenderer(colors=True)
        ]
        
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                clean_stdlib_keys,
                structlog.dev.ConsoleRenderer(colors=True)
            ]
        )


    # Configure structlog itself
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicate logging
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
        
    # Standard stdout handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)

    # Optional persistent file logging
    log_file = os.getenv("LOG_FILE")
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        from logging.handlers import RotatingFileHandler
        # 10MB per file, max 5 backups, UTF-8 encoding
        file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
        
        if log_format.upper() == "JSON":
            file_handler.setFormatter(formatter)
        else:
            # Persistent key-value rendering without terminal ANSI color escapes
            file_formatter = structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=shared_processors,
                processors=[
                    clean_stdlib_keys,
                    structlog.processors.KeyValueRenderer(key_order=["event"])
                ]
            )
            file_handler.setFormatter(file_formatter)
            
        root_logger.addHandler(file_handler)
        
    root_logger.setLevel(numeric_level)

    # Hijack other logger handlers and set propagation
    # This forces third-party libraries (like uvicorn, fastapi, sqlalchemy) to delegate to the root logger
    loggers_to_hijack = ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "sqlalchemy", "sqlalchemy.engine"]
    for name in loggers_to_hijack:
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True
        if "sqlalchemy" in name or name == "fastapi":
            logger.setLevel(logging.WARNING if log_level.upper() != "DEBUG" else logging.DEBUG)
        else:
            logger.setLevel(numeric_level)

