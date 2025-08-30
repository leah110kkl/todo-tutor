from rq.worker import Worker
from rq.job import Job
import multiprocessing
import time
import redis

REDIS_CONFIG = {
    "host": "127.0.0.1",
    "port": 6379,
    "db": 1,
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "decode_responses": False
}

def create_redis_conn_in_child():
    try:
        conn = redis.Redis(**REDIS_CONFIG)
        conn.ping()
        return conn
    except Exception as e:
        print(f"子进程Redis连接失败: {str(e)}")
        raise

def execute_job_independently(job_id):
    redis_conn = None
    try:
        # 1. 创建Redis连接
        redis_conn = create_redis_conn_in_child()
        # 2. 加载任务
        job = Job.fetch(job_id, connection=redis_conn)
        # 3. 核心逻辑（抓取网页、写入SQLite）
        job.perform()  
        # 4. 成功日志
        print(f"任务成功 - ID: {job.id}, URL: {job.args[0]}")

    except Exception as e:
        error_msg = str(e)
        # 失败日志
        print(f"任务失败 - ID: {job_id}, 错误: {error_msg}")
        raise  
    finally:
        # 关闭Redis连接
        if redis_conn:
            redis_conn.close()

class WindowsWorker(Worker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_redis_conn = self.connection

    def work(self, burst=False, **kwargs):
        queue_name = self.queues[0].name
        queue_key = f"rq:queue:{queue_name}"
        print(f"*** 启动Windows Worker，监听队列: {queue_name} (Redis DB: {REDIS_CONFIG['db']})")
        print(f"*** 按 Ctrl+C 停止Worker")

        try:
            while True:
                # 主进程从Redis取任务ID
                job_id_bytes = self.main_redis_conn.lpop(queue_key)
                if job_id_bytes:
                    job_id = job_id_bytes.decode('utf-8')
                    print(f"\n发现新任务 - ID: {job_id}")
                    
                    # 启动子进程执行任务
                    process = multiprocessing.Process(
                        target=execute_job_independently,
                        args=(job_id,)
                    )
                    process.start()
                    process.join()  
                else:
                    time.sleep(1)
                    print(".", end="", flush=True)
                if burst:
                    break

        except KeyboardInterrupt:
            print("\n\n收到停止信号，Worker正在退出...")
        finally:
            self.main_redis_conn.close()
            print("\nWorker已停止（主进程Redis连接已关闭）")

    # 兼容RQ的空方法，避免调用报错
    def fork_work_horse(self, job, queue):
        pass

    def handle_signal(self, sig_num, frame):
        pass