"""
db_operation.py - 数据库交互模块
负责 activity 表的创建、未处理数据查询、分类结果存储等核心逻辑

"""
import sqlite3
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

#路径配置
try:
    core_dir = Path(__file__).parent.parent.resolve()
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
        print(f"[INFO] 已添加目录到搜索路径: {core_dir}")
except Exception as e:
    print(f"[ERROR] 路径配置失败: {str(e)}")
    raise

#导入外部模块
try:
    from activity_raw import ActivityRawStorage
except ModuleNotFoundError:
    print("[ERROR] 未找到activity_raw模块，请检查目录结构是否正确")
    raise
except Exception as e:
    print(f"[ERROR] 导入ActivityRawStorage失败: {str(e)}")
    raise

#日志配置
logging.basicConfig(
    filename='nlp_classifier.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# SQL常量定义
CREATE_ACTIVITY_TABLE = """
CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_raw_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    publish_time DATETIME NOT NULL,
    source_type TEXT NOT NULL,
    career_paths TEXT NOT NULL,  
    top_2_paths TEXT NOT NULL,   
    create_time DATETIME NOT NULL,
    last_feedback_time DATETIME,
    FOREIGN KEY (activity_raw_id) REFERENCES activity_raw (raw_id)
);

-- 索引1：按发布时间倒序查询（用于按时间筛选活动）
CREATE INDEX IF NOT EXISTS idx_publish_time ON activity (publish_time DESC);
-- 索引2：按创建时间倒序查询（用于查看最新分类结果）
CREATE INDEX IF NOT EXISTS idx_create_time ON activity (create_time DESC);
"""

#数据库管理器类
class ActivityDBManager:
    def __init__(self):
        """初始化数据库管理器"""
        try:
            # 复用ActivityRawStorage数据库配置
            self.raw_storage = ActivityRawStorage()
            
            # 获取数据库路径
            if  hasattr(self.raw_storage, 'database'):
                self.db_path = self.raw_storage.conn.database
            else:
                self.db_path = "crawler_activity_raw.db"
            print(f"[INFO] 成功获取数据库路径: {self.db_path}")
            
            #验证数据库文件是否存在
            if not Path(self.db_path).exists():
                raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
            #初始化数据库连接
            self.conn = None
            self.init_db()
            
        except AttributeError as e:
            print(f"[ERROR] {str(e)}")
            raise
        except FileNotFoundError as e:
            print(f"[ERROR] {str(e)}")
            raise
        except Exception as e:
            print(f"[ERROR] 初始化数据库管理器失败: {str(e)}")
            raise
        
        
    def init_db(self) -> bool:
        """初始化数据库连接并创建activity表"""
        try:
            self.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False #允许跨线程使用连接
            )
            self.create_activity_table()
            logging.info(f"数据库初始化成功: {self.db_path}")
            return True
        except sqlite3.Error as e:
            error_msg = f"数据库连接失败 - 路径: {self.db_path}, 错误: {str(e)}"
            logging.error(error_msg)
            print(f"[ERROR] {error_msg}")
            return False
        except Exception as e:
            error_msg = f"数据库初始化失败 - 路径: {self.db_path}, 错误: {str(e)}"
            logging.error(error_msg)
            print(f"[ERROR] {error_msg}")
            return False
            
    def create_activity_table(self):
        """创建activity表及索引"""
        try:
            with self.conn:
                self.conn.executescript(CREATE_ACTIVITY_TABLE)
            logging.info("activity表创建成功")
        except Exception as e:
            logging.error(f"创建activity表失败: {str(e)}")
            raise
            
    def get_unprocessed_raw_activities(self) -> List[Dict]:
        """获取未处理的原始活动数据"""
        try:
            with self.conn:
                cursor = self.conn.execute("""
                    SELECT r.* FROM activity_raw r 
                    LEFT JOIN activity a ON r.id = a.activity_raw_id
                    WHERE a.id IS NULL AND r.crawl_status = 1
                    ORDER BY r.raw_publish_time DESC 
                """)
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor:
                    result = dict(zip(columns, row))
                    results.append(result)
                return results
        except Exception as e:
            logging.error(f"查询未处理活动失败: {str(e)}")
            return []
            
    def save_activity_result(self, 
        activity_raw_id: int,
        title: str,
        content: str, 
        publish_time: datetime,
        source_type: str,
        career_paths: Dict[str, float],
        top_2_paths: str
    ) -> bool:
        """保存活动分类结果到activity表"""
        try:
            with self.conn:
                self.conn.execute("""
                    INSERT INTO activity (
                        activity_raw_id, title, content, publish_time,
                        source_type, career_paths, top_2_paths,
                        create_time, last_feedback_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    activity_raw_id, title, content, publish_time,
                    source_type, json.dumps(career_paths), top_2_paths,
                    datetime.now(), None
                ))
            logging.info(f"保存分类结果成功 - 活动: {title}")
            return True
        except Exception as e:
            logging.error(f"保存分类结果失败: {str(e)}")
            return False
            
    def update_feedback_time(self, activity_id: int) -> bool:
        """更新活动的最后反馈时间"""
        try:
            with self.conn:
                self.conn.execute("""
                    UPDATE activity 
                    SET last_feedback_time = ?
                    WHERE id = ?
                """, (datetime.now(), activity_id))
            return True
        except Exception as e:
            logging.error(f"更新反馈时间失败: {str(e)}")
            return False
            
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logging.info("数据库连接已关闭")

# 全局实例
try:
    db_manager = ActivityDBManager()
except Exception as e:
    print(f"[ERROR] 创建数据库管理器实例失败: {str(e)}")
    raise