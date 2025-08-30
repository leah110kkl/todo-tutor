from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import time
import random
import re
from typing import Dict, Optional, List, Set
import redis
from urllib.parse import urljoin
from rq import Queue, Retry
from rq.job import Job
from activity_raw import storage_manager
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    filename='crawl_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

# 通用工具函数

def log_error(message: str, url: str) -> None:
    """记录错误信息到日志文件"""
    error_msg = f"URL: {url} - {message}"
    logging.error(error_msg)
    print(f"错误已记录: {error_msg}")

def create_redis_connection():
    """创建并返回Redis连接对象"""
    try:
        conn = redis.Redis(
            host=CONFIG["redis_host"],
            port=CONFIG["redis_port"],
            db=CONFIG["redis_queue_db"],
            decode_responses=False,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        conn.ping()
        print(f"Redis队列连接成功（DB: {CONFIG['redis_queue_db']}）")
        return conn
    except redis.ConnectionError as e:
        log_error(f"Redis连接失败：{str(e)}，请检查Redis是否启动且端口正确", "Redis Connection")
        raise
    except Exception as e:
        log_error(f"Redis连接异常：{str(e)}", "Redis Connection")
        raise

def is_peak_hour() -> bool:
    """判断当前是否处于高峰时段"""
    current_time = datetime.now().strftime("%H:%M")
    for period in CONFIG["peak_hours"]:
        if period["start"] <= current_time <= period["end"]:
            return True
    return False

def get_dynamic_delay(response_time: float, last_delay: float = None) -> float:
    """计算下一次请求的动态延迟时间"""
    if is_peak_hour():
        base_min, base_max = CONFIG["peak_delay_range"]
        print("当前处于高峰时段，使用较长延迟")
    else:
        base_min, base_max = CONFIG["delay_range"]

    if last_delay is None:
        return random.uniform(base_min, base_max)

    thresholds = CONFIG["response_thresholds"]
    adjustments = CONFIG["delay_adjustments"]
    
    if response_time > thresholds["slow"]:
        new_delay = last_delay + adjustments["increase"]
        print(f"响应时间较慢 ({response_time:.2f}s)，增加延迟")
    elif response_time < thresholds["fast"]:
        new_delay = last_delay - adjustments["decrease"]
        print(f"响应时间较快 ({response_time:.2f}s)，减少延迟")
    else:
        new_delay = last_delay
        
    new_delay = max(CONFIG["min_delay"], min(CONFIG["max_delay"], new_delay))
    variation = new_delay * 0.1
    final_delay = random.uniform(new_delay - variation, new_delay + variation)
    
    return round(final_delay, 2)

def is_domain_allowed(url: str, source_type: str) -> bool:
    """检查URL是否在指定数据源的允许域名列表中"""
    source_config = SOURCE_CONFIG.get(source_type)
    if not source_config:
        print(f"未知数据源类型：{source_type}")
        return False
        
    # 适配本地file协议URL
    if source_type == "校园官网" and url.startswith("file:///"):
        allowed_path = source_config["allowed_domains"][0]  # 本地路径作为允许域名
        if allowed_path in url:
            return True
        print(f"禁止抓取非允许本地路径：{url}")
        return False
    
    # 常规HTTP/HTTPS URL检查
    for domain in source_config["allowed_domains"]:
        if domain in url:
            return True
    print(f"禁止抓取非允许域名：{url}")
    return False

def check_robots_txt(url: str) -> bool:
    """从URL中提取域名，检查robots.txt"""
    from urllib.parse import urlparse
    parsed_url = urlparse(url)

    if parsed_url.scheme == "file":
        print("本地文件URL，跳过robots.txt检查")
        return True
    
    domain = parsed_url.netloc
    robots_url = f"{parsed_url.scheme}://{domain}/robots.txt"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=CONFIG["user_agent"])
            page.goto(robots_url, timeout=10000)
            robots_content = page.text_content() or ""
            browser.close()
            
            target_path = parsed_url.path
            # 检查是否被robots.txt禁止
            disallow_patterns = [
                f"Disallow: {target_path}",
                f"Disallow: {target_path.rstrip('/')}/",
                "Disallow: /notice/"  # 校园官网公告目录通用禁止规则
            ]
            if any(pattern in robots_content for pattern in disallow_patterns):
                print(f"robots.txt禁止抓取路径：{target_path}")
                return False
            return True
    except Exception as e:
        print(f"检查robots.txt失败（{e}），将谨慎抓取")
        return True

def get_redis_client() -> redis.Redis:
    """获取Redis客户端连接"""
    return redis.Redis(
        host=CONFIG["redis_host"],
        port=CONFIG["redis_port"],
        db=CONFIG["redis_db"],
        decode_responses=True
    )

def is_url_crawled(url: str, redis_client: redis.Redis) -> bool:
    """检查URL是否已经抓取过"""
    key = f"{CONFIG['redis_key_prefix']}{url}"
    return redis_client.exists(key)

def mark_url_crawled(url: str, redis_client: redis.Redis) -> None:
    """标记URL为已抓取"""
    key = f"{CONFIG['redis_key_prefix']}{url}"
    redis_client.setex(key, CONFIG["url_expire_days"] * 24 * 3600, "1")

def parse_publish_time(time_text: str, source_type: str) -> Optional[datetime]:
    """解析不同格式的发布时间"""
    source_config = SOURCE_CONFIG.get(source_type)
    if not source_config:
        return datetime.now()
        
    # 处理微信公众号“X小时前”“X天前”等相对时间
    if source_type == "微信公众号":
        # 匹配“1小时前”“2天前”
        hour_match = re.search(r'(\d+)小时前', time_text)
        day_match = re.search(r'(\d+)天前', time_text)
        if hour_match:
            hours_ago = int(hour_match.group(1))
            return datetime.now() - timedelta(hours=hours_ago)
        if day_match:
            days_ago = int(day_match.group(1))
            return datetime.now() - timedelta(days=days_ago)
    
    # 处理标准时间格式
    for time_format in source_config["time_formats"]:
        try:
            if "月" in time_text and "年" not in time_text:
                current_year = datetime.now().year
                time_text = f"{current_year}年{time_text}"
            return datetime.strptime(time_text.strip(), time_format)
        except ValueError:
            continue
            
    logging.warning(f"无法解析时间格式：{time_text}（来源：{source_type}）")
    return datetime.now()

def clean_content(content: str, source_type: str) -> str:
    """清理页面内容"""
    source_config = SOURCE_CONFIG.get(source_type)
    if not source_config:
        return content
        
    if source_type == "微信公众号":
        cleaned = content
        # 移除配置中的广告文本
        for ad_text in source_config.get("content_cleanup", []):
            cleaned = cleaned.replace(ad_text, "")
        # 移除微信公众号多余的换行和空格
        cleaned = re.sub(r'\n+', '\n', cleaned).strip()
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        return cleaned
        
    # 校园官网内容清理（移除多余HTML标签）
    # 保留p、a、br标签，移除其他标签
    cleaned = re.sub(r'<(?!p|a|br|/p|/a|/br)[^>]+>', '', content)
    # 移除多余换行
    cleaned = re.sub(r'\n+', '\n', cleaned).strip()
    return cleaned

# 核心抓取函数 

def get_detail_urls(list_url: str, source_type: str) -> Set[str]:
    """从列表页面获取所有详情页URL"""
    detail_urls = set()
    source_config = SOURCE_CONFIG.get(source_type)
    if not source_config:
        log_error(f"未知数据源类型：{source_type}", list_url)
        return detail_urls
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=CONFIG["user_agent"]
            )
            
            # 微信公众号使用 add_cookies添加Cookie
            if source_type == "微信公众号":
                cookies = source_config.get("cookies", {})
                if cookies and all(cookies.values()):  # 确保Cookie值不为空
                    cookie_list = []
                    for name, value in cookies.items():
                        cookie_list.append({
                            "name": name,
                            "value": value,
                            "domain": ".mp.weixin.qq.com",  # 微信公众号根域名，必须正确
                            "path": "/",
                            "httpOnly": True,  # 微信Cookie默认开启httpOnly
                            "secure": True,    # HTTPS链接必须开启secure
                            "sameSite": "Lax"  # 兼容现代浏览器SameSite策略
                        })
                    context.add_cookies(cookie_list)
                    print("微信公众号Cookie添加成功（使用add_cookies复数形式）")
                else:
                    log_error("微信公众号Cookie未配置或值为空，可能导致抓取失败", list_url)
                
            page = context.new_page()
            page.goto(list_url, timeout=30000)
            
            # 等待列表页元素加载
            selector = source_config["selectors"]["list"]["item_links"]
            try:
                page.wait_for_selector(selector, timeout=10000)
            except Exception as e:
                log_error(f"列表页元素加载超时（{selector}）: {str(e)}", list_url)
                browser.close()
                return detail_urls
            
            print("列表页加载完成，开始提取详情页URL")
            
            links = page.query_selector_all(selector)
            for link in links:
                href = link.get_attribute("href")
                if not href:
                    continue  # 跳过空链接
                
                # 适配校园官网本地file协议URL
                if source_type == "校园官网":
                    full_url = href if href.startswith("file:///") else urljoin(list_url, href)
                else:
                    # 微信公众号链接处理
                    full_url = urljoin("https://mp.weixin.qq.com", href) if not href.startswith("http") else href
                    
                if is_domain_allowed(full_url, source_type):
                    detail_urls.add(full_url)
            
            browser.close()
    except Exception as e:
        log_error(f"获取列表页URLs失败: {str(e)}", list_url)
    return detail_urls

def crawl_page(url: str, source_type: str) -> Optional[Dict[str, any]]:
    """合规抓取网页信息的主函数"""
    if not is_domain_allowed(url, source_type):
        log_error("URL不在允许域名列表中", url)
        return None

    source_config = SOURCE_CONFIG.get(source_type)
    if not source_config:
        log_error(f"未知数据源类型：{source_type}", url)
        return None

    last_delay = None
    last_response_time = None

    for retry in range(CONFIG["max_retries"] + 1):
        try:
            delay = get_dynamic_delay(last_response_time or 2, last_delay)
            last_delay = delay
            
            print(f"等待 {delay:.2f} 秒后开始抓取...")
            time.sleep(delay)

            start_time = time.time()
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=CONFIG["user_agent"]
                )
                
                # 微信公众号添加Cookie
                if source_type == "微信公众号":
                    cookies = source_config.get("cookies", {})
                    if cookies and all(cookies.values()):
                        cookie_list = []
                        for name, value in cookies.items():
                            cookie_list.append({
                                "name": name,
                                "value": value,
                                "domain": ".mp.weixin.qq.com",
                                "path": "/",
                                "httpOnly": True,
                                "secure": True,
                                "sameSite": "Lax"
                            })
                        context.add_cookies(cookie_list)
                
                page = context.new_page()
                # 增加页面加载超时处理
                try:
                    page.goto(url, timeout=30000)
                except Exception as e:
                    log_error(f"页面加载超时: {str(e)}", url)
                    browser.close()
                    raise
                
                last_response_time = time.time() - start_time

                selectors = source_config["selectors"]["detail"]
                
                # 提取页面数据
                result = {
                    "url": url,
                    "title": "未获取到标题",
                    "content": "未获取到正文",
                    "publish_time": datetime.now(),
                    "source": source_type,
                    "author": "未知作者",
                    "attach_urls": []
                }

                # 提取标题
                title_elem = page.query_selector(selectors["title"])
                if title_elem:
                    result["title"] = title_elem.text_content().strip() or result["title"]
                    print(f"成功提取标题：{result['title']}")
                else:
                    result["title"] = page.title().strip() or result["title"]

                # 提取发布时间
                time_elem = page.query_selector(selectors["publish_time"])
                if time_elem:
                    time_text = time_elem.text_content().strip()
                    result["publish_time"] = parse_publish_time(time_text, source_type)
                else:
                    log_error("未找到发布时间元素，使用当前时间", url)

                # 提取作者
                author_elem = page.query_selector(selectors["author"])
                if author_elem:
                    result["author"] = author_elem.text_content().strip() or result["author"]

                # 提取正文
                content_elem = page.query_selector(selectors["content"])
                if content_elem:
                    result["content"] = clean_content(
                        content_elem.inner_html(),
                        source_type
                    ) or result["content"]
                else:
                    log_error("未找到正文元素", url)

                # 提取附件
                attach_elems = page.query_selector_all(selectors["attachments"])
                for elem in attach_elems:
                    if source_type == "微信公众号":
                        # 微信文档链接（data-doc属性）
                        doc_url = elem.get_attribute("data-doc")
                        if doc_url:
                            result["attach_urls"].append(f"https://mp.weixin.qq.com/s/{doc_url}")
                    else:
                        # 校园官网附件链接（href属性）
                        href = elem.get_attribute("href")
                        if href:
                            full_url = urljoin(url, href)
                            result["attach_urls"].append(full_url)

                browser.close()

                # 准备存储参数
                publish_time_str = result["publish_time"].strftime("%Y-%m-%d %H:%M:%S")
                crawl_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 存储原始数据
                storage_success = storage_manager.save_to_activity_raw(
                    target_url=result["url"],
                    raw_title=result["title"],
                    raw_publish_time=publish_time_str,
                    raw_content=result["content"],
                    source_type=source_type,
                    crawl_time=crawl_time_str,
                    crawl_status=1,
                    raw_author=result.get("author"),
                    raw_attach_url=result.get("attach_urls"),
                    error_msg=None
                )

                if not storage_success:
                    print(f"警告：数据存储失败 - URL: {url}")

                return result

        except Exception as e:
            log_error(f"第 {retry+1} 次抓取失败: {str(e)}", url)
            
            fail_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # 存储失败记录
            storage_manager.save_to_activity_raw(
                target_url=url,
                raw_title="",
                raw_publish_time=fail_time_str,
                raw_content="",
                source_type=source_type,
                crawl_time=fail_time_str,
                crawl_status=0,
                error_msg=str(e)
            )
            
            if retry == CONFIG["max_retries"]:
                return None
            time.sleep(2)  # 重试前等待2秒

# 批量/异步抓取函数

def batch_crawl_sync(list_url: str, source: str) -> List[Dict[str, any]]:
    """同步批量抓取"""
    results = []
    
    try:
        redis_client = get_redis_client()
    except redis.ConnectionError as e:
        log_error("Redis连接失败，切换为本地模式", list_url)
        redis_client = None
    
    detail_urls = get_detail_urls(list_url, source)
    if not detail_urls:
        log_error("未找到任何详情页URL", list_url)
        return results

    print(f"共发现 {len(detail_urls)} 个详情页")
    
    for url in detail_urls:
        try:
            if redis_client and is_url_crawled(url, redis_client):
                print(f"跳过已抓取的URL: {url}")
                continue
                
            result = crawl_page(url, source)
            if result:
                results.append(result)
                if redis_client:
                    mark_url_crawled(url, redis_client)
        except Exception as e:
            log_error(f"处理URL失败: {str(e)}", url)
            continue
    
    return results

def batch_crawl(list_url: str, source_type: str) -> List[Dict[str, any]]:
    """同步批量抓取（临时跳过Redis检查）"""
    results = []
    detail_urls = get_detail_urls(list_url, source_type)
    if not detail_urls:
        log_error("未找到任何详情页URL", list_url)
        return results

    print(f"共发现 {len(detail_urls)} 个详情页")
    
    for url in detail_urls:
        try:
            result = crawl_page(url, source_type)
            if result:
                results.append(result)
        except Exception as e:
            log_error(f"处理URL失败: {str(e)}", url)
            continue
    
    return results

def get_queue_connection() -> redis.Redis:
    """获取RQ队列专用的Redis连接"""
    return create_redis_connection()

def create_retry_strategy() -> Retry:
    """创建RQ任务重试策略"""
    return Retry(
        max=CONFIG["max_task_retries"],
        interval=CONFIG["task_retry_interval"]
    )

def get_task_queue() -> Queue:
    """获取任务队列实例"""
    return Queue(CONFIG["queue_name"], connection=REDIS_CONN)

def add_crawl_tasks(url_list: List[str], source: str) -> List[Job]:
    """将URL列表添加到抓取队列"""
    queue = get_task_queue()
    jobs = []
    
    # 避免循环导入，在函数内部导入
    from crawl_jobs import crawl_worker
    retry_strategy = create_retry_strategy()

    for url in url_list:
        if is_domain_allowed(url, source):
            job = queue.enqueue(
                crawl_worker,
                args=(url, source),
                job_timeout='10m',
                retry=retry_strategy,
                meta={
                    'config': CONFIG,
                    'retry_interval': CONFIG["task_retry_interval"]
                }
            )
            jobs.append(job)
            print(f"已添加任务 - ID: {job.id}, URL: {url}")
    
    return jobs

def monitor_jobs(jobs: List[Job], timeout: int = 3600) -> List[Dict]:
    """监控任务执行状态并获取结果"""
    start_time = time.time()
    results = []
    pending_jobs = jobs.copy()
    
    while pending_jobs and (time.time() - start_time) < timeout:
        for job in pending_jobs[:]:  
            try:
                job.refresh()  # 刷新任务状态
            except UnicodeDecodeError:
                job_data = job.connection.hgetall(job.key)
                status_bytes = job_data.get(b'status', b'')
                job._data = status_bytes.decode('utf-8', errors='replace')
            
            if job.is_finished:
                try:
                    result = job.result
                    if isinstance(result, bytes):
                        result = result.decode('utf-8', errors='replace')
                    results.append(result)
                except:
                    results.append(None)
                pending_jobs.remove(job)
                print(f"任务完成 - ID: {job.id}")
            elif job.is_failed:
                print(f"任务失败 - ID: {job.id}")
                pending_jobs.remove(job)
                
        if pending_jobs:
            time.sleep(5)  # 等待5秒后检查
            
    return results

def batch_crawl_real_async(list_url: str, source: str) -> List[Dict]:
    """真正的异步批量抓取：任务入队并监控结果"""
    try:
        REDIS_CONN.ping()
    except redis.ConnectionError as e:
        error_msg = f"Redis未连接：{str(e)}，无法执行异步抓取"
        log_error(error_msg, list_url)
        print(error_msg)
        return []
    
    detail_urls = get_detail_urls(list_url, source)
    if not detail_urls:
        log_error("未找到任何详情页URL", list_url)
        return []

    print(f"共发现 {len(detail_urls)} 个详情页，开始加入异步队列")
    jobs = add_crawl_tasks(list(detail_urls), source)
    if not jobs:
        print("未添加任何异步任务")
        return []

    print("开始监控异步任务执行状态...")
    results = monitor_jobs(jobs, timeout=600)
    return results

# 配置与全局变量

# 可配置参数
CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "delay_range": (1, 3),
    "max_retries": 2,
    "redis_host": "localhost",
    "redis_port": 6379,
    "redis_db": 0,
    "redis_key_prefix": "crawled_urls:",
    "url_expire_days": 7,
    "redis_queue_db": 1,
    "queue_name": "crawl_tasks",
    "max_task_retries": 3,
    "task_retry_interval": 60,
    "worker_name": "crawler_worker"
}

# 数据源专用配置
SOURCE_CONFIG = {
    "校园官网": {
        "allowed_domains": ["file:///[电脑路径]/[项目根目录]/test_resources/"],  # 测试
        "selectors": {
            "list": {
                "item_links": "a.notice-item, a.notice-link",
                "next_page": ".pagination .next"
            },
            "detail": {
                "title": "h1.notice-title",
                "publish_time": ".publish-time",
                "author": ".author",
                "content": ".notice-content",
                "attachments": "a[href$='.pdf'], a[href$='.doc'], a[href$='.docx']"
            }
        },
        "time_formats": [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d"
        ]
    },
    "微信公众号": {
        "allowed_domains": ["mp.weixin.qq.com"],
        "cookies": {  # 存放登录态Cookie
            "wxuin": "YOUR_WXUIN",
            "wxsid": "YOUR_WXSID",
            "pass_ticket": "YOUR_PASS_TICKET"
        },
        "selectors": {
            "list": {
                "item_links": "a.weui-msg-card",
                "next_page": "#next_page"
            },
            "detail": {
                "title": "#activity-name",
                "publish_time": "#publish-time",
                "author": "#js_name",
                "content": "#js_content",
                "attachments": "a[data-doc]"
            }
        },
        "time_formats": [
            "%Y-%m-%d %H:%M:%S",
            "%Y年%m月%d日",
            "%m月%d日"  
        ],
        "content_cleanup": [
            "关注我们",
            "长按识别二维码",
            "点击上方蓝字"
        ]
    }
}

# 补充配置参数
CONFIG.update({
    "source_config": SOURCE_CONFIG,
    "delay_range": (1, 3),  
    "peak_delay_range": (5, 8),  
    "peak_hours": [  
        {"start": "09:00", "end": "11:30"},
        {"start": "14:00", "end": "17:00"}
    ],
    "min_delay": 1,  
    "max_delay": 10,  
    "response_thresholds": {  
        "slow": 3,  
        "fast": 1   
    },
    "delay_adjustments": {  
        "increase": 1.0,   
        "decrease": 0.5    
    },
})

# 初始化全局Redis连接
REDIS_CONN = create_redis_connection()

# 测试函数(修改)
if __name__ == "__main__":
    try:
        test_cases = [
            {
                "source_type": "校园官网",
                "list_url": "file:///[电脑路径]/[项目根目录]/test_resources/local_notice_list.html"
            },
            {
                "source_type": "微信公众号",
                "list_url": "https://mp.weixin.qq.com/mp/homepage?__biz=xxx&hid=xxx"
            }
        ]
        
        for test_case in test_cases:
            print(f"\n===== 测试{test_case['source_type']}抓取 =====")
            results = batch_crawl(test_case["list_url"], test_case["source_type"])
            print(f"抓取完成，成功获取 {len(results)} 条数据")
            
            for i, result in enumerate(results[:2], 1):
                print(f"\n第{i}条数据：")
                print(f"标题：{result['title']}")
                print(f"发布时间：{result['publish_time']}")
                print(f"来源：{result['source']}")
                print(f"URL：{result['url']}")
                
    except Exception as e:
        print(f"\n测试过程出错：{str(e)}")
        log_error(f"测试代码执行失败: {str(e)}", "test_main")
    finally:
        storage_manager.close()
        print("\n测试结束，数据库连接已关闭")
