import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 创建logs目录（如果不存在）
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 创建格式化器
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 创建文件处理器
file_handler = RotatingFileHandler(
    log_dir / "app.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(formatter)

# 创建控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# 创建应用日志记录器
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    return logger 