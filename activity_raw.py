import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
import json

# 配置日志
logging.basicConfig(
    filename='activity_raw_storage.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# SQLite表结构定义
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS activity_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  /* 自增主键，唯一标识每条记录 */
    target_url TEXT NOT NULL UNIQUE,           /* 目标页面URL，唯一约束避免重复 */
    raw_title TEXT NOT NULL,                   /* 活动标题原文，用于NLP关键词提取 */
    raw_publish_time TEXT NOT NULL,            /* 原始发布时间（字符串格式：YYYY-MM-DD HH:MM:SS） */
    raw_content TEXT NOT NULL,                 /* 完整页面内容，NLP分类核心数据 */
    source_type TEXT NOT NULL,                 /* 数据来源，用于来源可信度权重 */
    crawl_time TEXT NOT NULL,                  /* 抓取时间（字符串格式：YYYY-MM-DD HH:MM:SS） */
    crawl_status INTEGER NOT NULL,             /* 抓取状态(1成功/0失败) */
    raw_author TEXT,                          /* 可选：发布单位，用于主体权重 */
    raw_attach_url TEXT,                      /* 可选：附件URL(逗号分隔) */
    error_msg TEXT,                           /* 可选：抓取失败原因 */
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP  /* 可选：记录创建时间 */
); 
CREATE INDEX IF NOT EXISTS idx_publish_time ON activity_raw (raw_publish_time DESC);  
CREATE INDEX IF NOT EXISTS idx_crawl_time ON activity_raw (crawl_time DESC);          
"""

class ActivityRawStorage:
    def __init__(self, db_path="crawler_activity_raw.db"):
        """初始化数据库连接"""
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            print(f" SQLite数据库连接成功: {db_path}")
            # 初始化表结构
            self.create_table()
        except sqlite3.Error as e:
            logging.error(f" 数据库连接失败: {str(e)}")
            raise  # 抛出异常

    def create_table(self):
        """创建activity_raw表（统一使用CREATE_TABLE_SQL，确保表结构唯一）"""
        try:
            with self.conn:
                self.conn.executescript(CREATE_TABLE_SQL)
            print(" activity_raw表结构初始化完成（含索引）")
        except sqlite3.OperationalError as e:
            # 表已存在时不报错（仅打印提示），其他错误正常抛出
            if "already exists" in str(e).lower():
                print(" activity_raw表已存在，无需重复创建")
            else:
                logging.error(f" 创建表失败: {str(e)}")
                raise
        except Exception as e:
            logging.error(f" 创建表异常: {str(e)}")
            raise

    def save_to_activity_raw(self, **kwargs) -> bool:
        """保存数据到activity_raw表（修复插入逻辑字段不匹配问题）"""
        # 1. 必选字段校验
        required_fields = [
            'target_url', 'raw_title', 'raw_publish_time',
            'raw_content', 'source_type', 'crawl_time', 'crawl_status'
        ]
        
        for field in required_fields:
            # 校验字段是否存在
            if field not in kwargs:
                msg = f"缺失必选字段: {field} - 当前传递的字段：{list(kwargs.keys())}"
                logging.warning(msg)
                print(f"⚠️ {msg}")
                return False
            # 校验字段值是否为空
            if not kwargs[field] and field not in ['error_msg', 'raw_author', 'raw_attach_url']:
                msg = f"必选字段 {field} 值为空 - 当前值：{kwargs[field]}"
                logging.warning(msg)
                print(f"⚠️ {msg}")
                return False
            # 校验时间字段类型
            if field in ['raw_publish_time', 'crawl_time'] and not isinstance(kwargs[field], str):
                msg = f"字段 {field} 类型错误：需字符串，实际是 {type(kwargs[field])}"
                logging.warning(msg)
                print(f"⚠️ {msg}")
                return False

        try:
            # 2. 处理附件URL列表
            if 'raw_attach_url' in kwargs:
                if isinstance(kwargs['raw_attach_url'], list):
                    kwargs['raw_attach_url'] = ','.join(kwargs['raw_attach_url']) if kwargs['raw_attach_url'] else ""
                    logging.debug(f"附件列表已转为字符串：{kwargs['raw_attach_url']}")
                elif kwargs['raw_attach_url'] is None:
                    kwargs['raw_attach_url'] = ""

            # 3. 处理error_msg
            if 'error_msg' not in kwargs:
                kwargs['error_msg'] = None

            with self.conn:
                # 4. 检查URL是否已存在
                cursor = self.conn.execute(
                    "SELECT id FROM activity_raw WHERE target_url = ?",
                    (kwargs['target_url'],)
                )
                existing_record = cursor.fetchone()

                if existing_record:
                    # 5. 更新现有记录
                    update_values = [
                        kwargs['raw_title'],
                        kwargs['raw_content'],
                        kwargs['crawl_time'],
                        kwargs['crawl_status'],
                        kwargs.get('raw_author', ""),
                        kwargs['raw_attach_url'],
                        kwargs['error_msg'],
                        kwargs['target_url']  # WHERE条件：目标URL
                    ]

                    self.conn.execute("""
                        UPDATE activity_raw
                        SET raw_title=?, raw_content=?, crawl_time=?,
                            crawl_status=?, raw_author=?, raw_attach_url=?,
                            error_msg=?
                        WHERE target_url=?
                    """, update_values)
                    print(f"ℹ️ 更新原始数据成功: {kwargs['target_url']}")

                else:
                    # 6. 插入新记录
                    allowed_fields = [
                        'target_url', 'raw_title', 'raw_publish_time', 'raw_content',
                        'source_type', 'crawl_time', 'crawl_status', 'raw_author',
                        'raw_attach_url', 'error_msg'
                    ]
                    filtered_kwargs = {k: v for k, v in kwargs.items() if k in allowed_fields}
                    placeholders = ','.join(['?' for _ in filtered_kwargs])
                    fields = ','.join(filtered_kwargs.keys())  # 用过滤后的字段，避免多余字段
                    values = list(filtered_kwargs.values())

                    # 打印调试信息
                    logging.debug(f"INSERT 字段：{fields}，值数量：{len(values)}，占位符数量：{placeholders.count('?')}")
                    self.conn.execute(
                        f"INSERT INTO activity_raw ({fields}) VALUES ({placeholders})",
                        values
                    )
                    print(f"✅ 存储原始数据成功: {kwargs['target_url']}")

            return True

        except Exception as e:
            # 打印详细错误信息
            error_msg = (
                f"存储失败 - URL: {kwargs.get('target_url', 'unknown')}, "
                f"参数：{str(kwargs)}, 错误: {str(e)}"
            )
            logging.error(error_msg, exc_info=True)  
            print(f"❌ {error_msg}")
            return False
    
    def query_activity_raw(self, condition: str = "") -> List[Dict]:
        """查询activity_raw表数据（保留原有逻辑，确保返回格式正确）"""
        try:
            with self.conn:
                cursor = self.conn.execute(
                    f"SELECT * FROM activity_raw {condition}"
                )
                columns = [description[0] for description in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    result = dict(zip(columns, row))
                    # 转换附件URL字符串回列表
                    if result.get('raw_attach_url'):
                        result['raw_attach_url'] = result['raw_attach_url'].split(',')
                    results.append(result)
                
                print(f" 查询activity_raw表成功，共获取 {len(results)} 条数据")
                return results
        except Exception as e:
            logging.error(f" 查询失败: {str(e)}", exc_info=True)
            return []

    def close(self):
        """关闭数据库连接（确保资源释放）"""
        if self.conn:
            self.conn.close()
            print(" SQLite连接已关闭")

# 全局存储管理器实例（供外部模块导入使用）
storage_manager = ActivityRawStorage()

def test_storage():
    """测试数据存储功能"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 测试成功数据
    success_data = {
        "target_url": "https://example.com/notice/1",
        "raw_title": "测试公告（成功）",
        "raw_publish_time": current_time,
        "raw_content": "这是一个测试公告的详细内容，用于验证存储功能是否正常...",
        "source_type": "测试来源",
        "crawl_time": current_time,
        "crawl_status": 1,
        "raw_author": "测试部门",
        "raw_attach_url": ["http://example.com/file1.pdf", "http://example.com/file2.doc"]
    }

    # 测试失败数据
    fail_data = {
        "target_url": "https://example.com/notice/2",
        "raw_title": "测试公告（失败）",  
        "raw_publish_time": current_time,
        "raw_content": "抓取失败，无正文内容",
        "source_type": "测试来源",
        "crawl_time": current_time,
        "crawl_status": 0,
        "error_msg": "连接超时（测试用）",
        "raw_author": None,
        "raw_attach_url": None
    }

    try:
        print("\n=== 开始测试数据存储 ===")
        # 存储测试数据
        success_result = storage_manager.save_to_activity_raw(**success_data)
        print(f"成功数据存储结果: {' 成功' if success_result else ' 失败'}")
        
        fail_result = storage_manager.save_to_activity_raw(**fail_data)
        print(f"失败数据存储结果: {' 成功' if fail_result else ' 失败'}")

        # 查询验证
        print("\n=== 开始测试数据查询 ===")
        all_records = storage_manager.query_activity_raw()
        print(f"总记录数: {len(all_records)}")

        # 查询成功记录
        success_records = storage_manager.query_activity_raw("WHERE crawl_status = 1")
        print(f"成功记录数: {len(success_records)}")
        if success_records:
            record = success_records[0]
            print(f"成功记录标题: {record['raw_title']}")
            print(f"成功记录发布时间: {record['raw_publish_time']}")
            print(f"成功记录附件数: {len(record['raw_attach_url']) if record['raw_attach_url'] else 0}")

    except Exception as e:
        print(f"\n 测试过程中出错: {str(e)}")
    finally:
        storage_manager.close()
        print("\n=== 测试结束 ===")

if __name__ == "__main__":
    test_storage()

