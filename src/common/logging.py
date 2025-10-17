"""
Logging setup with rich console output and UI bridge.
"""

import sys
from loguru import logger
from rich.console import Console
from rich.theme import Theme
from typing import Optional
from pathlib import Path

# Custom theme for rich console
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold",
    "debug": "dim",
})

console = Console(theme=custom_theme)

# Configure loguru
logger.remove()  # Remove default handler

# Add console handler with rich formatting
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Add file handler for persistent logs
log_file = Path("logs/app.log")
log_file.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    log_file,
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)


class UILogBridge:
    """Bridge to send logs to UI (NiceGUI)."""
    
    def __init__(self):
        self.callbacks = []
    
    def register_callback(self, callback):
        """Register a callback to receive log messages."""
        self.callbacks.append(callback)
    
    def emit(self, level: str, message: str):
        """Emit a log message to all registered callbacks."""
        for callback in self.callbacks:
            try:
                callback(level, message)
            except Exception as e:
                logger.error(f"Error in log callback: {e}")


# Global UI log bridge
ui_log_bridge = UILogBridge()


def log_to_ui(level: str, message: str):
    """Log message to UI."""
    ui_log_bridge.emit(level, message)


# Custom logger functions that also send to UI
def info(message: str, to_ui: bool = False):
    """Log info message."""
    logger.info(message)
    if to_ui:
        log_to_ui("info", message)


def warning(message: str, to_ui: bool = False):
    """Log warning message."""
    logger.warning(message)
    if to_ui:
        log_to_ui("warning", message)


def error(message: str, to_ui: bool = False):
    """Log error message."""
    logger.error(message)
    if to_ui:
        log_to_ui("error", message)


def success(message: str, to_ui: bool = False):
    """Log success message."""
    logger.success(message)
    if to_ui:
        log_to_ui("success", message)


def debug(message: str, to_ui: bool = False):
    """Log debug message."""
    logger.debug(message)
    if to_ui:
        log_to_ui("debug", message)

