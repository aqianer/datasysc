import json
from itertools import islice
from pathlib import Path
from sqlalchemy import create_engine, text
import logging
from datetime import datetime


class MySQLBatchLoader:
    def __init__(self, table_schema, logger=None):
        self.logger = logger
        self.engine = get_database_engine(logger)  # 使用配置文件创建引擎
        self.table_config = self._parse_schema(table_schema)  # 解析表结构定义文件

    def _chunk_generator(self, data_dir, batch_size=1000):
        """JSON文件分批加载器"""
        for json_file in Path(data_dir).glob('*.json'):
            with open(json_file, 'r', encoding='utf-8') as f:
                while chunk := list(islice(f, batch_size)):
                    yield [json.loads(line) for line in chunk]

    def _transform_data(self, raw_data):
        """数据格式转换"""
        return [{
            'event_time': item['timestamp'],
            'source_system': item['source'],
            'raw_data': json.dumps(item['data']),
            'checksum': self._calculate_hash(item)
        } for item in raw_data]

    def run(self, data_dir):
        """主执行流程"""
        if self.logger:
            self.logger.info(f"开始处理目录: {data_dir}")
            
        with self.engine.connect() as conn:
            for batch in self._chunk_generator(data_dir):
                try:
                    transformed = self._transform_data(batch)
                    conn.execute(text(self._generate_insert_sql()), transformed)
                    conn.commit()
                    if self.logger:
                        self.logger.debug(f"成功插入一批数据，大小: {len(batch)}")
                except Exception as e:
                    conn.rollback()
                    if self.logger:
                        self.logger.error(f"批量插入失败: {str(e)}", exc_info=True)
                    self._save_failed_batch(batch)

def load_config():
    """加载配置文件"""
    current_dir = Path(__file__).parent
    config_path = current_dir / 'config.json'
    
    if not config_path.exists():
        raise FileNotFoundError("配置文件 'config.json' 不存在")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_database_engine(logger):
    """获取数据库引擎"""
    try:
        # 从配置文件加载数据库配置
        config = load_config()
        db_config = config['database']
        
        # 构建数据库URL
        url = f"mysql+pymysql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config['charset']}"
        engine = create_engine(url, echo=False)
        logger.info("数据库连接成功")
        return engine
    except Exception as e:
        logger.error(f"获取数据库引擎失败: {e}", exc_info=True)
        raise

def save_toggl_data_to_db(data, engine, logger):
    """将Toggl数据保存到MySQL数据库
    
    Args:
        data: Toggl API返回的JSON数据
        engine: SQLAlchemy数据库引擎
        logger: 日志记录器
    """
    try:
        # 准备插入的数据
        insert_data = {            
            'toggl_accounts_id': data.get('toggl_accounts_id'),
            'clients': json.dumps(data.get('clients', []), ensure_ascii=False),
            'time_entries': json.dumps(data.get('time_entries', []), ensure_ascii=False),
            'workspace_list': json.dumps(data.get('workspaces', []), ensure_ascii=False),
            'tag_list': json.dumps(data.get('tags', []), ensure_ascii=False),
            'project_list': json.dumps(data.get('projects', []), ensure_ascii=False),
            'create_time': datetime.now(),
            'update_time': datetime.now()
        }
        
        # SQL插入语句
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
        
        # 执行插入
        with engine.connect() as conn:
            result = conn.execute(text(insert_sql), insert_data)
            conn.commit()
            logger.info(f"Toggl数据已保存到数据库，ID: {result.lastrowid}")
            
    except Exception as e:
        logger.error(f"保存Toggl数据到数据库失败: {e}", exc_info=True)
        raise

def process_saved_toggl_data(data_dir, engine, logger):
    """处理保存的Toggl数据文件并写入数据库
    
    Args:
        data_dir: 数据目录路径
        engine: 数据库引擎
        logger: 日志记录器
    """
    try:
        # 遍历数据目录
        data_path = Path(data_dir)
        for json_file in data_path.glob('**/toggl/user_data_*.json'):
            logger.info(f"处理文件: {json_file}")
            
            # 读取JSON文件
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 保存到数据库
            save_toggl_data_to_db(data, engine, logger)
            
    except Exception as e:
        logger.error(f"处理Toggl数据文件失败: {e}", exc_info=True)
        raise