# 活动数据采集与NLP多路径打分系统
## Activity Data Crawler & NLP Career-Path Scoring System

## 1. 项目简介 (Project Overview)
基于Python开发的一体化系统，整合**校园活动数据采集**、**NLP文本分类**与**多生涯路径重要度打分**功能。该系统支持合规抓取校园官网/微信公众号活动信息，通过RQ+Redis实现异步任务管理，结构化数据存入SQLite，再通过“规则+ML模型融合”计算活动对多生涯路径的重要度得分，为个性化推荐提供数据支撑。
A Python-based all-in-one system that combines **campus activity data crawling**, **NLP text classification**, and **career-path importance scoring**. It supports compliant crawling of campus official websites and WeChat Official Accounts, uses RQ+Redis for asynchronous task management, stores structured data in SQLite, and calculates activity importance scores for multiple career paths (postgraduate exam, employment, etc.) via "rule + ML model fusion" — providing data support for personalized recommendations.  



## 2. 核心功能 (Core Features)
| 模块 (Module)               |  核心功能 (Key Functions)                                                                 |
|-----------------------------|------------------------------------------------------------------------------------------|
|  数据采集 (Data Crawling)    | 1. Crawl from campus websites, WeChat Official Accounts, and local HTML<br>2. Compliance: `allowed_domains` whitelist, `robots.txt` check<br>3. Anti-crawl: Dynamic delay (5-8s peak / 1-3s off-peak), failure retry<br>4. Async: RQ+Redis task queue; Redis deduplicates crawled URLs (7-day retention)<br>5. Storage: Structured data saved to SQLite |
|  NLP多路径打分 (NLP & Career-Path Scoring) | 1. Score activities for 5 career paths: 考研 (postgraduate), 就业 (employment), 考公 (public exam), 留学 (study abroad), 创业 (entrepreneurship)<br>2. Scoring logic: "keyword rule + ML model" weighted calculation<br>3. Feedback optimization: Adjust model weights via user behavior (e.g., stay time)<br>4. Output: Path scores (0-10) + Top 2 high-importance paths |


## 3. 项目结构 (Project Structure)
```
core/  
├─ # Data Crawling Module / 数据采集模块
├─ crawl_framework.py   # Core: Playwright crawling, dynamic delay, RQ wrapper
├─ activity_raw.py      # Storage: SQLite init & data writing
├─ crawl_jobs.py        # Task: RQ task functions (Windows-compatible)
├─ custom_worker.py     # Worker: Custom RQ Worker (Windows-compatible)
├─ # NLP Classification Module / NLP分类模块
├─ nlp_module/          
│  ├─ db_operation.py   # NLP data interaction with SQLite
│  ├─ nlp_classifier.py # Core: Career-path scoring logic
│  ├─ feedback_handler.py # Feedback: Adjust weights via user behavior
│  ├─ test_module.py    # NLP function testing
│  └─ requirements_nlp.txt # NLP-specific dependencies
├─ # Auxiliary Files / 辅助文件
├─ README.md            # User guide (this file)
├─ requirements.txt     # Core dependencies
└─ crawl_errors.log     # Crawling error logs (auto-generated)
```


## 4. 环境准备 (Environment Preparation)
### 4.1 安装依赖 (Install Dependencies)
先确保已安装Python 3.13，再执行以下命令安装核心依赖与NLP依赖：
First, ensure Python 3.13 is installed. Then install core dependencies and NLP-specific dependencies:
```bash

# 安装核心依赖 / Install core dependencies
pip install -r requirements.txt

# 安装Playwright浏览器驱动（必执行） / Install Playwright browser drivers
playwright install

# 安装NLP依赖 / Install NLP dependencies
pip install -r nlp_module/requirements_nlp.txt
```

####  依赖说明 (Dependencies Note)
- Core dependencies (`requirements.txt`):  
  `python==3.13`, `playwright==1.54.0`, `rq==1.9.0`, `redis==6.4.0`  
  - SQLite: Built into Python 3.13 (no extra installation; use `import sqlite3` directly)  
- NLP dependencies (`requirements_nlp.txt`):  
  `jieba>=0.42.1`, `transformers>=4.41.0`, `torch>=2.3.0` (for text classification)


### 4.2  Redis配置（必选）(Redis Configuration)
  Redis用于RQ任务队列与已爬URL去重，需安装并启动：
  Redis is used for RQ task queues and crawled URL deduplication. Install and start Redis:
- **Windows**:  
  Download [Memurai](https://www.memurai.com/) (recommended) or [Redis for Windows](https://github.com/tporadowski/redis/releases). Check "Add to PATH" during installation.  
- **Mac**:  
  `brew install redis`  
- **Linux**:  
  `sudo apt install redis-server`  

####  启动并验证Redis (Start & Verify Redis)
```bash
# 启动Redis服务（保持终端运行） / Start Redis service
redis-server

# 新终端验证连接（返回PONG即正常） / New terminal: Verify connection (returns "PONG" if successful)
redis-cli ping
```


### 4.3 启动RQ Worker (Start RQ Worker)
用于处理异步采集任务（适配Windows）：
For asynchronous crawling tasks (Windows-compatible): 
```bash
# 在core目录下执行 / Run in core directory
rq worker --url redis://127.0.0.1:6379/1 \
  --name crawler_worker \
  crawl_tasks \
  --worker-class custom_worker.WindowsWorker190
```
- Success sign / 成功标志: Terminal shows "Listening for work on crawl_tasks"


## 5. 快速使用 (Quick Start)
### 5.1 数据采集 (Data Crawling)
#### Step 1: 配置数据源 (Configure Data Source)
修改`crawl_framework.py`中的`SOURCE_CONFIG`（将占位符替换为实际信息）：
Edit `SOURCE_CONFIG` in `crawl_framework.py` (replace placeholders with your actual info): 
```python
SOURCE_CONFIG = {
    "校园官网": {
        # 替换为你的本地测试路径或校园官网域名
        # Replace with your local test path or campus website domain
        "allowed_domains": ["file:///C:/Users/YourName/Project/core/test_resources/"],
        "selectors": {  # 按目标页面结构调整 / Adjust based on target page structure
            "list": {"item_links": "a.notice-item", "next_page": ".pagination .next"},
            "detail": {"title": "h1.notice-title", "content": ".notice-content"}
        },
        "time_formats": ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
    },
    "微信公众号": {
        "allowed_domains": ["mp.weixin.qq.com"],
        # 登录微信公众号后，通过浏览器开发者工具获取最新Cookie
        # Get latest cookies via browser dev tools (after logging in to WeChat MP)
        "cookies": {
            "wxuin": "Your_WXUIN",
            "wxsid": "Your_WXSID",
            "pass_ticket": "Your_Pass_Ticket"
        },
        "selectors": {
            "list": {"item_links": "a.weui-msg-card"},
            "detail": {"title": "#activity-name", "content": "#js_content"}
        }
    }
}
```

#### Step 2:  执行采集任务 (Run Crawling Task)  
在`crawl_framework.py`末尾添加测试代码，调用采集函数：
Call crawling functions in `crawl_framework.py` (add test code at the end of the file):
```python
if __name__ == "__main__":
    # Option 1: Sync crawling (for testing) / 方式1：同步采集（测试用）
    sync_results = batch_crawl(
        list_url="https://notice.your-school.edu.cn/list",  # Campus notice list URL
        source_type="校园官网"  # Match SOURCE_CONFIG key
    )
    print(f"Sync crawl done: {len(sync_results)} items")

    # Option 2: Async crawling (recommended for large tasks) / 方式2：异步采集（大任务推荐）
    # async_results = batch_crawl_real_async(
    #     list_url="https://mp.weixin.qq.com/...",  # WeChat MP list URL
    #     source="微信公众号"
    # )
    # print(f"Async crawl done: {len(async_results)} items")
```

执行采集命令：
Run the crawler:
```bash
python crawl_framework.py
```


### 5.2 NLP多路径打分 (NLP Career-Path Scoring)
#### Step 1: 准备输入数据 (Prepare Input Data)
使用采集到的数据（来自SQLite `activity_raw`表）或测试文本：
Use crawled data (from SQLite `activity_raw` table) or test text:
- Input: Activity `title` (str) + `content` (str)  
- Output: `path_scores` (dict) + `top_2_paths` (list)

#### Step 2: 测试NLP打分 (Test NLP Scoring)
在`nlp_module/nlp_classifier.py`中添加测试代码：
Add test code in `nlp_module/nlp_classifier.py`:
```python
if __name__ == "__main__":
    from nlp_classifier import CareerPathClassifier  # Import classifier

    # 初始化分类器 / Initialize classifier
    classifier = CareerPathClassifier()

    # 测试文本（校园活动） / Test text (campus activity)
    test_title = "2025考研复试指导会通知"
    test_content = "本次指导会讲解考研复试流程、专业课复习重点及调剂技巧，欢迎报考同学参加。"

    # 获取得分 / Get scores
    path_scores, top_2_paths = classifier.classify_text(test_title, test_content)

    # 打印结果 / Print results
    print("Career Path Scores / 各路径得分:", path_scores)
    # 示例输出 / Example output : {"考研": 9.2, "就业": 3.5, "考公": 2.0, "留学": 1.8, "创业": 1.0}
    print("Top 2 High-Importance Paths / Top2高重要度路径:", top_2_paths)
    # 示例输出 / Example output : ["考研", "就业"]
```
执行测试命令：
Run the test:  
```bash
cd core/nlp_module
python nlp_classifier.py
```


## 6. 常见问题 (FAQ)
| 问题现象 (Issue)                |  解决方法 (Solution)                                                                 |
|---------------------------------|-------------------------------------------------------------------------------------|
| Redis连接失败 (Redis Connection Failed) | 1. Check if Redis service is running (`redis-server`)<br>2. Use Memurai (Windows) to avoid WSL port conflicts<br>3. Restart Redis or change port (default: 6379) |
| 微信公众号抓取失败 (WeChat MP Crawling Failed) | 1. Update `cookies` in `SOURCE_CONFIG` (get via browser dev tools after login)<br>2. Adjust `selectors` if WeChat page structure changes<br>3. Reduce crawl frequency if IP is blocked |
| NLP得分异常 (Abnormal NLP Scores) | 1. Add more keywords in `nlp_classifier.py` (e.g., add "调剂" for 考研 path)<br>2. Verify `jieba` installation (`pip list | grep jieba`)<br>3. Check if text has valid keywords (empty scores mean no matching keywords) |
| SQLite文件未生成 (SQLite File Not Generated) | 1. Ensure `activity_raw.py` uses correct path (`Path(__file__).parent` points to `core`)<br>2. Check if `core` directory has write permission<br>3. Verify crawling task succeeded (see `crawl_errors.log`) |


## 7. 日志与数据查看 (Logs & Data View)
- **Crawling Logs**: `core/crawl_errors.log` (records failed URLs and error reasons)  
- **SQLite Data**: Use [DB Browser for SQLite](https://sqlitebrowser.org/) to open `core/crawler_activity_raw.db` (view `activity_raw` table)  
- **Redis Deduplication**: Run `redis-cli -n 0 keys "crawled_urls:*"` to check crawled URLs