from typing import Dict, Optional
import time
from rq import get_current_job  

# 从主脚本导入crawl_page
from crawl_framework import crawl_page, log_error  

def crawl_worker(url: str, source: str) -> Optional[Dict]:
    """ RQ任务函数（适配Windows + RQ 1.9.0）"""
    # 从当前任务的meta中获取CONFIG
    job = get_current_job()
    config = job.meta.get('config', {})
    max_retries = config.get("max_task_retries", 3)
    retry_interval = config.get("task_retry_interval", 60)
    
    for attempt in range(max_retries + 1):
        try:
            # 调用导入的crawl_page
            result = crawl_page(url, source)
            if result:
                print(f"任务成功 - ID: {job.id}, URL: {url}")
                return result
            raise Exception("抓取结果为空")
        except Exception as e:
            error_msg = f"第{attempt+1}次失败: {str(e)}"
            log_error(error_msg, url)
            if attempt < max_retries:
                print(f"等待{retry_interval}秒后重试...")
                time.sleep(retry_interval)
            else:
                print(f"已达最大重试次数 - ID: {job.id}, URL: {url}")
                raise  # 抛出异常，RQ记录失败状态