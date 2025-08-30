import logging
from datetime import datetime
from db_operation import db_manager
from nlp_classifier import classifier
from feedback_handler import feedback_handler

def test_classification_pipeline():
    """测试完整的分类流程"""
    try:
        #打印数据库路径
        print(f"[DEBUG] db_manager 连接的数据库路径：{db_manager.db_path}")

        # 1. 获取未处理的活动
        raw_activities = db_manager.get_unprocessed_raw_activities()
        if not raw_activities:
            print("[ERROR] activity_raw表无数据,请先执行Ingestion模块抓取数据")
            return
            
        # 2. 测试第一条数据
        test_activity = raw_activities[0]
        print(f"\n[INFO] 测试活动: {test_activity['raw_title']}")
        
        # 3. 执行分类
        path_scores, top_2_paths = classifier.classify_text(
            test_activity['raw_title'],
            test_activity['raw_content']
        )
        print("\n[INFO] 分类结果:")
        for path, score in path_scores.items():
            print(f"- {path}: {score}分")
        print(f"- 主要路径: {top_2_paths}")
        
        # 4. 保存分类结果
        save_success = db_manager.save_activity_result(
            activity_raw_id=test_activity['id'],
            title=test_activity['raw_title'],
            content=test_activity['raw_content'],
            publish_time=test_activity['raw_publish_time'],
            source_type=test_activity['source_type'],
            career_paths=path_scores,
            top_2_paths=top_2_paths
        )
        if save_success:
            print("\n[INFO] 分类结果已保存到activity表")
            
        # 5. 模拟用户反馈
        feedback_path = top_2_paths.split(",")[0]  # 使用得分最高的路径
        user_score = path_scores[feedback_path] + 1  # 模拟用户给出更高分
        
        feedback_success = feedback_handler.handle_score_feedback(
            activity_id=1,  
            path=feedback_path,
            user_score=user_score,
            current_score=path_scores[feedback_path]
        )
        if feedback_success:
            print(f"\n[INFO] 用户反馈已处理:")
            print(f"- 路径: {feedback_path}")
            print(f"- 原始得分: {path_scores[feedback_path]}")
            print(f"- 用户反馈: {user_score}")
            print(f"- 规则权重: {classifier.rule_weight:.2f}")
            print(f"- 模型权重: {classifier.model_weight:.2f}")
            
    except Exception as e:
        print(f"[ERROR] 测试过程出错: {str(e)}")
    finally:
        db_manager.close()

if __name__ == "__main__":
    test_classification_pipeline()