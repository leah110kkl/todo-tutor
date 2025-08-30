import logging
from typing import Dict
from datetime import datetime
from db_operation import db_manager
from nlp_classifier import classifier, CAREER_PATHS

# 配置日志
logging.basicConfig(
    filename='nlp_classifier.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

#用户行为反馈处理器
class FeedbackHandler:
    def __init__(self):
        """初始化反馈处理器"""
        self.min_weight = 0.0
        self.max_weight = 1.0
        self.weight_step = 0.1
        self.behavior_threshold = 180  # 用户行为阈值（例：停留时间180秒，可按需修改）
        
    def handle_behavior_feedback(self, 
        activity_id: int,
        path: str,
        behavior_value: float,
        current_score: float
    ) -> bool:
        """处理用户对活动-路径重要度的反馈
        Args:
            activity_id: 活动ID
            path: 生涯路径
            behavior_score: 用户行为的量化值（停留秒数）
            current_score: 当前系统计算的分数
        Returns:
            bool: 反馈处理是否成功
        """
        try:
            if path not in CAREER_PATHS:
                logging.error(f"无效的生涯路径: {path}")
                return False
                
            # 计算行为倾向（
            need_increase_rule_weight = None
            if behavior_value > self.behavior_threshold:
                need_increase_rule_weight = True  # 行为表明重要度应更高
            elif behavior_value < self.behavior_threshold / 3:
                need_increase_rule_weight = False  # 行为表明重要度应更低
                
            # 基于行为倾向调整权重
            if need_increase_rule_weight is not None:
                if need_increase_rule_weight:
                    # 用户行为表明应更高分，增加规则权重
                    classifier.rule_weight = min(
                        self.max_weight,
                        classifier.rule_weight + self.weight_step
                    )
                    classifier.model_weight = max(
                        self.min_weight,
                        classifier.model_weight - self.weight_step
                    )
                else:
                    # 用户行为表明应更低分，增加模型权重
                    classifier.model_weight = min(
                        self.max_weight,
                        classifier.model_weight + self.weight_step
                    )
                    classifier.rule_weight = max(
                        self.min_weight,
                        classifier.rule_weight - self.weight_step
                    )
                    
            # 更新数据库中的反馈时间
            db_manager.update_feedback_time(activity_id)
            
            logging.info(f"""
                反馈处理完成 - 活动ID: {activity_id}, 路径: {path}
                用户行为值: {behavior_value}, 系统得分: {current_score}
                新规则权重: {classifier.rule_weight:.2f}
                新模型权重: {classifier.model_weight:.2f}
            """)
            return True
            
        except Exception as e:
            logging.error(f"处理反馈失败: {str(e)}")
            return False

# 全局反馈处理器实例            
feedback_handler = FeedbackHandler()