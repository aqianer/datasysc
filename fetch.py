import aiohttp
import asyncio
import json
import base64
import requests
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from data_loader import get_database_engine, save_toggl_data_to_db, process_saved_toggl_data

def setup_logging():
    """配置日志系统"""
    # 获取当前文件所在目录
    current_dir = Path(__file__).parent
    # 创建logs目录
    logs_dir = current_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # 生成日志文件名（按日期）
    log_file = logs_dir / f"{datetime.now().strftime('%Y%m%d')}.log"
    
    # 配置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置日志处理器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    # 获取logger实例
    logger = logging.getLogger('DataSync')
    return logger

def load_config():
    # 获取当前文件所在目录
    current_dir = Path(__file__).parent
    config_path = current_dir / 'config.json'
    
    if not config_path.exists():
        raise FileNotFoundError("配置文件 'config.json' 不存在")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

async def fetch_github_data(user, api_type='events', logger=None):
    """获取GitHub数据
    
    Args:
        user: GitHub用户名
        api_type: API类型 ('events' 或 'actions')
        logger: 日志记录器
    """
    logger.info(f"开始获取GitHub用户 {user} 的{api_type}数据")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # 根据API类型设置URL
    api_urls = {
        'events': f'https://api.github.com/users/{user}/events'
        # 'actions': f'https://api.github.com/users/{user}/actions'
    }
    
    if api_type not in api_urls:
        logger.error(f"不支持的API类型: {api_type}")
        return None
    
    async with aiohttp.ClientSession() as session:
        try:
            logger.debug(f"发送请求到GitHub API: {api_urls[api_type]}")
            async with session.get(api_urls[api_type], headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                
                # 生成时间戳和保存路径
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                date = datetime.now().strftime("%Y%m%d")
                data_dir = setup_data_directory('github', date)
                
                # 保存数据到文件
                filename = data_dir / f"{api_type}_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"GitHub {api_type} 数据已保存到文件: {filename}")
                
                return data
        except Exception as e:
            logger.error(f"获取GitHub {api_type} 数据失败: {e}", exc_info=True)
            return None

def setup_data_directory(source=None, date=None):
    """创建并返回数据目录路径
    
    Args:
        source: 数据源名称 ('github' 或 'toggl')
        date: 日期字符串，默认为当天 (格式: YYYYMMDD)
    """
    # 获取当前文件所在目录（datasysc）
    current_dir = Path(__file__).parent
    # 基础数据目录
    data_dir = current_dir / 'data'
    
    # 如果没有提供日期，使用当天日期
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 解析日期为年/月/日
    year = date[:4]
    month = date[4:6]
    day = date[6:8]
    
    # 如果提供了数据源，创建对应的子目录
    if source:
        # 创建年/月/日/数据源的目录结构
        target_dir = data_dir / year / month / day / source
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir
    
    # 如果没有提供数据源，返回日期目录
    date_dir = data_dir / year / month / day
    date_dir.mkdir(parents=True, exist_ok=True)
    return date_dir

def fetch_toggl_data(api_token, logger):
    """获取Toggl用户数据，包含相关数据"""
    logger.info("开始获取Toggl用户数据")
    auth = base64.b64encode(f"{api_token}:api_token".encode()).decode("ascii")
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Basic {auth}'
    }
    
    try:
        # 获取完整的用户信息（包含相关数据）
        logger.debug("发送请求到Toggl API，获取用户完整信息")
        params = {'with_related_data': 'true'}
        response = requests.get(
            'https://api.track.toggl.com/api/v9/me',
            headers=headers,
            params=params
        )
        response.raise_for_status()
        data = response.json()
        
        # 生成时间戳和保存路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date = datetime.now().strftime("%Y%m%d")
        data_dir = setup_data_directory('toggl', date)
        
        # 保存用户完整信息
        filename = data_dir / f"user_data_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Toggl用户数据已保存到文件: {filename}")
        
        return data
    except Exception as e:
        logger.error(f"获取Toggl数据失败: {e}", exc_info=True)
        return None

def get_toggl_api_token(email, password):
    """获取Toggl API token和用户信息"""
    auth = base64.b64encode(f"{email}:{password}".encode()).decode("ascii")
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Basic {auth}'
    }
    
    try:
        response = requests.get('https://api.track.toggl.com/api/v9/me', headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # 生成时间戳和目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date = datetime.now().strftime("%Y%m%d")
        data_dir = setup_data_directory('toggl', date)
        
        # 保存用户信息
        user_filename = data_dir / f"user_info_{timestamp}.json"
        with open(user_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Toggl用户信息已保存到文件: {user_filename}")
        
        return {
            'api_token': data.get('api_token'),
            'default_workspace_id': data.get('default_workspace_id')
        }
    except Exception as e:
        print(f"获取API token失败: {e}")
        return None

def update_config_token(email, password):
    """更新配置文件中的API token和default_workspace_id"""
    current_dir = Path(__file__).parent
    config_path = current_dir / 'config.json'
    
    # 读取现有配置
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {"github": {"username": ""}, "toggl": {}}
    
    # 获取API token和workspace_id
    toggl_info = get_toggl_api_token(email, password)
    if toggl_info:
        config['toggl']['api_token'] = toggl_info['api_token']
        config['toggl']['default_workspace_id'] = toggl_info['default_workspace_id']
        # 保存更新后的配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print("API token和default_workspace_id已更新到配置文件")
        return True
    return False

if __name__ == "__main__":
    try:
        # 设置日志
        logger = setup_logging()
        logger.info("开始数据同步任务")
        
        # 加载配置
        config = load_config()
        logger.debug("配置文件加载成功")
        
        # 创建数据库引擎
        engine = get_database_engine(logger)
        
        # 如果API token为空，则尝试获取
        if not config['toggl'].get('api_token'):
            logger.info("Toggl API token不存在，尝试获取新token")
            if update_config_token(
                config['toggl']['email'],
                config['toggl']['password']
            ):
                logger.info("Token更新成功")
                config = load_config()
            else:
                logger.error("Token更新失败")
                exit(1)
        
        # GitHub数据获取
        github_events = asyncio.run(fetch_github_data(
            config['github']['username'],
            api_type='events',
            logger=logger
        ))
        
        # Toggl数据获取
        toggl_result = fetch_toggl_data(config['toggl']['api_token'], logger)
        
        # 处理并保存Toggl数据到数据库
        current_dir = Path(__file__).parent
        data_dir = current_dir / 'data'
        process_saved_toggl_data(data_dir, engine, logger)
        
        logger.info("数据同步任务完成")
    
    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
    except KeyError as e:
        logger.error(f"配置文件格式错误: 缺少必要的配置项 {e}")
    except Exception as e:
        logger.error(f"发生未知错误: {e}", exc_info=True)
