import aiohttp
import asyncio
import json
import base64
import requests
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text
import pytz

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
    """加载配置文件"""
    current_dir = Path(__file__).parent
    config_path = current_dir / 'config.json'
    
    if not config_path.exists():
        raise FileNotFoundError("配置文件 'config.json' 不存在")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def setup_data_directory(source=None, date=None):
    """创建并返回数据目录路径"""
    current_dir = Path(__file__).parent
    data_dir = current_dir / 'data'
    
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    year = date[:4]
    month = date[4:6]
    day = date[6:8]
    
    if source:
        target_dir = data_dir / year / month / day / source
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir
    
    date_dir = data_dir / year / month / day
    date_dir.mkdir(parents=True, exist_ok=True)
    return date_dir

def get_database_engine(logger):
    """获取数据库引擎"""
    try:
        config = load_config()
        db_config = config['database']
        
        url = f"mysql+pymysql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config['charset']}"
        engine = create_engine(url, echo=False)
        logger.info("数据库连接成功")
        return engine
    except Exception as e:
        logger.error(f"获取数据库引擎失败: {e}", exc_info=True)
        raise

async def fetch_github_data(user, api_type='events', logger=None):
    """获取GitHub数据"""
    logger.info(f"开始获取GitHub用户 {user} 的{api_type}数据")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    api_urls = {
        'events': f'https://api.github.com/users/{user}/events'
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
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                date = datetime.now().strftime("%Y%m%d")
                data_dir = setup_data_directory('github', date)
                
                filename = data_dir / f"{api_type}_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"GitHub {api_type} 数据已保存到文件: {filename}")
                
                return data
        except Exception as e:
            logger.error(f"获取GitHub {api_type} 数据失败: {e}", exc_info=True)
            return None

def fetch_toggl_data(api_token, logger):
    """获取Toggl用户数据，包含相关数据"""
    logger.info("开始获取Toggl用户数据")
    auth = base64.b64encode(f"{api_token}:api_token".encode()).decode("ascii")
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Basic {auth}'
    }
    
    try:
        logger.debug("发送请求到Toggl API，获取用户完整信息")
        params = {'with_related_data': 'true'}
        response = requests.get(
            'https://api.track.toggl.com/api/v9/me',
            headers=headers,
            params=params
        )
        response.raise_for_status()
        data = response.json()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        date = datetime.now().strftime("%Y%m%d")
        data_dir = setup_data_directory('toggl', date)
        
        filename = data_dir / f"user_data_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Toggl用户数据已保存到文件: {filename}")
        
        return data, filename  # 返回数据和文件路径
    except Exception as e:
        logger.error(f"获取Toggl数据失败: {e}", exc_info=True)
        return None, None

def save_toggl_data_to_db(data, engine, logger):
    """将Toggl数据保存到MySQL数据库"""
    try:
        insert_data = {
            'user_id':1,            
            'toggl_accounts_id': data.get('toggl_accounts_id'),
            'clients': json.dumps(data.get('clients', []), ensure_ascii=False),
            'time_entries': json.dumps(data.get('time_entries', []), ensure_ascii=False),
            'workspace_list': json.dumps(data.get('workspaces', []), ensure_ascii=False),
            'tag_list': json.dumps(data.get('tags', []), ensure_ascii=False),
            'project_list': json.dumps(data.get('projects', []), ensure_ascii=False),
            'create_time': datetime.now(),
            'update_time': datetime.now()
        }
        
        insert_sql = """
        INSERT INTO toggl_datas (
            user_id, toggl_accounts_id, clients, time_entries, 
            workspace_list, tag_list, project_list, 
            create_time, update_time
        ) VALUES (
            :user_id, :toggl_accounts_id, :clients, :time_entries,
            :workspace_list, :tag_list, :project_list,
            :create_time, :update_time
        )
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(insert_sql), insert_data)
            conn.commit()
            logger.info(f"Toggl数据已保存到数据库，ID: {result.lastrowid}")
            
    except Exception as e:
        logger.error(f"保存Toggl数据到数据库失败: {e}", exc_info=True)
        raise

def update_config_token(email, password):
    """更新配置文件中的API token"""
    auth = base64.b64encode(f"{email}:{password}".encode()).decode("ascii")
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Basic {auth}'
    }
    
    try:
        response = requests.get('https://api.track.toggl.com/api/v9/me', headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # 读取现有配置
        config = load_config()
        config['toggl']['api_token'] = data.get('api_token')
        
        # 保存更新后的配置
        current_dir = Path(__file__).parent
        config_path = current_dir / 'config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"获取API token失败: {e}")
        return False

def save_github_events_to_db(events_data, engine, logger):
    """将GitHub事件数据保存到数据库
    
    Args:
        events_data: GitHub API返回的事件数据列表
        engine: SQLAlchemy数据库引擎
        logger: 日志记录器
    """
    try:
        for event in events_data:
            # 转换时间格式
            event_time = datetime.strptime(
                event['created_at'], 
                '%Y-%m-%dT%H:%M:%SZ'
            ).replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Shanghai'))
            
            # 准备基础数据
            insert_data = {
                'user_id': 1,  # 这里需要替换为实际的用户ID
                'github_user_id': event['actor']['id'],
                'event_type': event['type'],
                'repo_id': event['repo']['id'],
                'repo_name': event['repo']['name'],
                'repo_url': f"https://github.com/{event['repo']['name']}",
                'event_time': event_time,  # 使用转换后的时间
                'commit_count': 0,
                'code_changes': '{}',
                'event_specific': '{}'
            }
            
            # 处理特定事件类型的数据
            if event['type'] == 'PushEvent':
                insert_data['commit_count'] = len(event['payload'].get('commits', []))
                # 这里可以添加代码变更统计的处理
                
            # 保存事件特有数据
            event_specific = {}
            if event['type'] == 'PullRequestEvent':
                pr_data = event['payload']['pull_request']
                event_specific['PullRequest'] = {
                    'action': event['payload']['action'],
                    'number': pr_data['number'],
                    'state': pr_data['state'],
                    'comments': pr_data.get('comments', 0)
                }
            elif event['type'] == 'IssuesEvent':
                issue_data = event['payload']['issue']
                event_specific['Issue'] = {
                    'number': issue_data['number'],
                    'title': issue_data['title']
                }
            
            insert_data['event_specific'] = json.dumps(event_specific)
            
            # 执行插入
            insert_sql = """
            INSERT INTO github_events (
                user_id, github_user_id, event_type, repo_id, 
                repo_name, repo_url, event_time, commit_count,
                code_changes, event_specific
            ) VALUES (
                :user_id, :github_user_id, :event_type, :repo_id,
                :repo_name, :repo_url, :event_time, :commit_count,
                :code_changes, :event_specific
            )
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(insert_sql), insert_data)
                conn.commit()
                logger.debug(f"GitHub事件已保存到数据库，ID: {result.lastrowid}")
        
        logger.info(f"成功保存 {len(events_data)} 条GitHub事件数据")
            
    except Exception as e:
        logger.error(f"保存GitHub事件数据到数据库失败: {e}", exc_info=True)
        raise

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
        
        # GitHub数据获取和保存
        github_events = asyncio.run(fetch_github_data(
            config['github']['username'],
            api_type='events',
            logger=logger
        ))
        if github_events:
            save_github_events_to_db(github_events, engine, logger)
        
        # Toggl数据获取和保存
        toggl_data, toggl_file = fetch_toggl_data(config['toggl']['api_token'], logger)
        if toggl_data:
            save_toggl_data_to_db(toggl_data, engine, logger)
        
        logger.info("数据同步任务完成")
    
    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
    except KeyError as e:
        logger.error(f"配置文件格式错误: 缺少必要的配置项 {e}")
    except Exception as e:
        logger.error(f"发生未知错误: {e}", exc_info=True) 