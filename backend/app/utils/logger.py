import sys

from loguru import logger

from app.config import settings


def setup_logging() -> None:
    logger.remove()
    level = "DEBUG" if settings.debug else "INFO"
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    )
    try:
        from pathlib import Path

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        logger.add(
            log_dir / "app.log",
            rotation="10 MB",
            retention="7 days",
            level=level,
        )
    except OSError:
        pass
