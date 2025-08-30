import json
import logging
from typing import Dict, List, Tuple
import jieba
from pathlib import Path
import time
from datetime import datetime
from .db_operation import db_manager

logging.basicConfig(
    filename='nlp_classifier.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# 停用词表
STOP_WORDS = {
    "的", "了", "在", "是", "和", "及", "等", "为", "将", "举办", "通知",
    "有", "与", "到", "从", "这", "那", "就", "于", "由", "与", "向",
    "也", "但", "而", "或", "如", "该", "每", "其", "些", "此", "都",
    "着", "并", "很", "中", "更", "好", "还", "以", "把", "我", "你",
    "他", "它", "们", "个", "让", "给", "要", "后", "前", "已", "能",
    "看", "到", "对", "上", "下", "再", "被", "又", "时", "过", "现"
}

# 路径定义
CAREER_PATHS = ["考研", "就业", "考公", "留学", "创业"]

# 动态权重阈值
SHORT_TEXT_THRESHOLD = 50
LONG_TEXT_THRESHOLD = 200

# 路径基础分
PATH_BASE_SCORES = {
    "考研": 1.0,
    "就业": 1.0,
    "考公": 0.8,
    "留学": 0.8,
    "创业": 0.5
}

# 关键词
KEYWORDS = {
    "考研": {
        "高权重": [
            "考研", "考上岸", "硕士", "研究生",
            "调剂", "复试", "研究生考试", "考研大纲",
            "考研英语", "考研数学", "考研政治", "专业课",
            "考研调剂", "考研报名", "考研初试", "考研复试"
        ],
        "中权重": [
            "专业课", "英语一", "数学", "政治",
            "数学一", "数学二", "英语二", "学硕",
            "专硕", "考研群", "考研机构", "考研资料",
            "考研真题", "考研学习", "备考指导"
        ],
        "低权重": [
            "复习", "备考", "考试",
            "笔记", "题库", "报考", "分数线",
            "考研论坛", "考研经验", "学习方法"
        ]
    },
    "就业": {
        "高权重": [
            "就业", "招聘", "面试", "简历",
            "校招", "秋招", "春招", "内推",
            "offer", "工作机会", "就业指导",
            "就业信息", "就业推荐", "就业形势"
        ],
        "中权重": [
            "实习", "秋招", "春招", "offer",
            "五险一金", "社保", "公积金", "年终奖",
            "薪资", "待遇", "职位", "岗位",
            "就业市场", "就业政策", "就业形势"
        ],
        "低权重": [
            "岗位", "工作", "求职",
            "简历指导", "面试技巧", "职业规划",
            "就业指南", "就业咨询", "就业服务",
            "就业培训", "就业能力"
        ]
    },
    "考公": {
        "高权重": [
            "公务员", "考公", "国考", "省考",
            "选调生", "公考", "事业编", "编制",
            "公务员考试", "公务员面试", "公职"
        ],
        "中权重": [
            "行测", "申论", "事业单位", "选调生",
            "面试班", "国考班", "省考班", "公基",
            "常识判断", "数量关系", "言语理解",
            "面试真题", "结构化面试"
        ],
        "低权重": [
            "政府", "机关", "公职",
            "公考资料", "考试真题", "考试技巧",
            "报考指南", "备考经验", "考试大纲"
        ]
    },
    "留学": {
        "高权重": [
            "留学", "海外", "雅思", "托福",
            "GRE", "GMAT", "留学申请", "签证",
            "offer", "海外院校", "国际教育"
        ],
        "中权重": [
            "申请", "文书", "语言", "国际",
            "推荐信", "GPA", "成绩单", "留学中介",
            "奖学金", "留学费用", "留学规划",
            "海外生活", "海外就业"
        ],
        "低权重": [
            "外国", "出国", "海外",
            "语言考试", "留学咨询", "留学指南",
            "留学经验", "留学生活", "海外交流"
        ]
    },
    "创业": {
        "高权重": [
            "创业", "创新", "项目", "商业",
            "创业计划", "融资", "商业计划书", "投资",
            "创业补贴", "孵化器", "众创空间"
        ],
        "中权重": [
            "孵化", "投资", "营销", "竞赛",
            "营业执照", "工商注册", "创业政策",
            "创业指导", "创业咨询", "创业培训",
            "创业孵化", "创业服务"
        ],
        "低权重": [
            "市场", "管理", "策划",
            "创业项目", "创业经验", "创业指南",
            "创业平台", "创业资源", "创业大赛"
        ]
    }
}

# 负向关键词
NEGATIVE_KEYWORDS = {
    "考研": ["就业", "招聘", "秋招", "春招", "国考", "省考", "留学", "创业"],
    "就业": ["考研", "复试", "调剂", "国考", "省考", "出国", "创业"],
    "考公": ["考研", "复试", "校招", "秋招", "托福", "雅思", "创业"],
    "留学": ["考研", "公务员", "招聘", "秋招", "创业", "国考"],
    "创业": ["考研", "公务员", "秋招", "春招", "雅思", "托福"]
}

# 补充关键词
ADDITIONAL_KEYWORDS = {
    "考研": {
        "高权重": ["保研", "推免", "研究生调剂系统", "考研复试指导会"],
        "中权重": ["考研讲座", "考研经验分享会", "专业课复习"],
        "低权重": ["成绩查询", "专业介绍", "导师信息"]
    },
    "就业": {
        "高权重": ["校招宣讲会", "简历优化", "职业规划讲座"],
        "中权重": ["求职经验分享", "行业介绍", "岗位推荐"],
        "低权重": ["就业指导", "职场经验", "求职技巧"]
    },
    "考公": {
        "高权重": ["国考报名", "省考笔试", "事业单位考试", "省考笔试培训"],
        "中权重": ["公考备考", "公考资料", "面试辅导"],
        "低权重": ["公职生涯", "公考经验", "考公指南"]
    },
    "留学": {
        "高权重": ["留学申请", "托福考试", "雅思考试", "留学文书"],
        "中权重": ["海外院校", "签证指导", "语言培训"],
        "低权重": ["留学经验", "海外生活", "国际交流"]
    },
    "创业": {
        "高权重": ["创业项目", "创业大赛", "创业孵化"],
        "中权重": ["商业计划", "创业指导", "项目路演"],
        "低权重": ["创业经验", "创新创业", "企业管理"]
    }
}

for path in ADDITIONAL_KEYWORDS:
    if path not in KEYWORDS:
        KEYWORDS[path] = {"高权重": [], "中权重": [], "低权重": []}
    for level in ["高权重", "中权重", "低权重"]:
        KEYWORDS[path][level].extend(ADDITIONAL_KEYWORDS[path][level])
        KEYWORDS[path][level] = list(dict.fromkeys(KEYWORDS[path][level]))


class CareerPathClassifier:
    def __init__(self):
        """初始化分类器"""
        self.rule_weight = 0.7  # 规则得分权重
        self.model_weight = 0.3  # 模型得分权重
        self._path_feature_words = {}  # 路径特征词集缓存
        self._init_feature_words()  # 预处理特征词集
        
    def _init_feature_words(self):
        """初始化各路径的特征词集"""
        for path in CAREER_PATHS:
            self._path_feature_words[path] = set(
            word for level in ["高权重", "中权重", "低权重"]
            for word in KEYWORDS[path].get(level, [])
        )
    
    def _get_effective_words(self, text: str) -> List[str]:
        """获取文本的有效词"""
        for path in CAREER_PATHS:
            for level in ["高权重", "中权重", "低权重"]:
                for phrase in KEYWORDS[path][level]:
                    if len(phrase) > 2 and phrase in text:
                        text = text.replace(phrase, f"__{phrase}__")  # 标记短语，避免拆分

        # jieba分词
        words = jieba.lcut(text)
        # 过滤停用词和单字
        return [w for w in words if w not in STOP_WORDS and len(w) > 1]
            
    def calculate_rule_score(self, text: str, path: str) -> float:
        """计算规则匹配得分（优化版）"""
        try:
            # 获取路径关键词
            path_keywords = KEYWORDS.get(path, {})
            if not path_keywords:
                return PATH_BASE_SCORES.get(path, 0.0)
                
            # 统计词频（限制单词最大次数为3）
            word_freq = {}
            effective_words = self._get_effective_words(text)
            for word in effective_words:
                if word in word_freq:
                    word_freq[word] = min(word_freq[word] + 1, 3)
                else:
                    word_freq[word] = 1
                    
            # 计算加权得分
            total_score = 0
            for word, freq in word_freq.items():
                if word in path_keywords["高权重"]:
                    total_score += 3 * freq
                elif word in path_keywords["中权重"]:
                    total_score += 2 * freq
                elif word in path_keywords["低权重"]:
                    total_score += 1 * freq
                    
            # 处理负向关键词
            if path in NEGATIVE_KEYWORDS:
                neg_score = 0
                for neg_word in NEGATIVE_KEYWORDS[path]:
                    if neg_word in word_freq:
                        neg_score += 2 * word_freq[neg_word]
                total_score = max(0, total_score - neg_score)
                
            # 动态归一化
            max_possible_score = len(path_keywords["高权重"]) * 3 * 3  # 假设每个高权重词出现3次
            normalized_score = (total_score / max_possible_score) * 10
            final_score = min(10, normalized_score)
            
            # 得分截断（低于2分按0分）
            if final_score < 2.0:
                return max(0.0, PATH_BASE_SCORES.get(path, 0.0))
                
            return round(final_score, 2)
            
        except Exception as e:
            logging.error(f"规则得分计算失败: {str(e)}")
            return PATH_BASE_SCORES.get(path, 0.0)
        
    def calculate_model_score(self, text: str, path: str) -> float:
        """计算语义匹配得分"""
        try:
            # 获取有效词
            effective_words = self._get_effective_words(text)
            if not effective_words:
                return 3.0  # 无有效词时返回3分
                
            # 获取路径特征词
            path_words = self._path_feature_words.get(path, set())
            if not path_words:
                return 3.0
                
            # 计算匹配词占比
            matched_words = set(effective_words) & path_words
            word_ratio = len(matched_words) / len(effective_words)
            ratio_score = word_ratio * 5
            
            # 计算加权匹配得分
            weight_score = 0
            max_weight_score = len(effective_words) * 3  # 最大可能得分
            
            for word in matched_words:
                if word in KEYWORDS[path]["高权重"]:
                    weight_score += 3
                elif word in KEYWORDS[path]["中权重"]:
                    weight_score += 2
                elif word in KEYWORDS[path]["低权重"]:
                    weight_score += 1
                    
            if max_weight_score > 0:
                weight_score = (weight_score / max_weight_score) * 5
            
            # 合并两个指标
            final_score = min(10, ratio_score + weight_score)
            
            # 得分截断
            if final_score < 2.0:
                return max(0.0, PATH_BASE_SCORES.get(path, 0.0))
                
            return round(final_score, 2)
            
        except Exception as e:
            logging.error(f"语义得分计算失败: {str(e)}")
            return 3.0
            
    def classify_text(self, title: str, content: str) -> Tuple[Dict[str, float], str]:
        """对活动进行多路径分类
        Args:
            title: 活动标题
            content: 活动正文
        Returns:
            Dict[str, float]: 各路径得分字典
            str: 得分最高的两个路径(逗号分隔)
        """
        # 合并标题和正文
        full_text = title * 3 + "\n" + content
        
        # 计算有效词数量并动态调整权重
        effective_words = self._get_effective_words(full_text)
        word_count = len(effective_words)
        
        if word_count < SHORT_TEXT_THRESHOLD:
            self.rule_weight = 0.8
            self.model_weight = 0.2
        elif word_count > LONG_TEXT_THRESHOLD:
            self.rule_weight = 0.6
            self.model_weight = 0.4
        else:
            self.rule_weight = 0.7
            self.model_weight = 0.3
            
        # 计算各路径得分
        path_scores = {}
        for path in CAREER_PATHS:
            rule_score = self.calculate_rule_score(full_text, path)
            model_score = self.calculate_model_score(full_text, path)
            
            # 加权平均
            final_score = round(
                rule_score * self.rule_weight + 
                model_score * self.model_weight,
                2
            )
            
            if final_score < 2.0 and final_score > PATH_BASE_SCORES[path]:
                final_score = 0.0
            path_scores[path] = max(final_score, PATH_BASE_SCORES[path])
            
        # 获取得分最高的两个路径
        sorted_paths = sorted(
            path_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        top_2_paths = ",".join([p[0] for p in sorted_paths[:2]])
        
        return path_scores, top_2_paths

    def batch_process(self) -> Dict[str, int]:
        """批量处理未分类的活动数据
        Returns:
            Dict[str, int]: 处理统计结果
        """
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }
        
        start_time = time.time()
        logging.info("开始批量处理未分类活动...")
        
        try:
            # 1. 获取未处理数据
            activities = db_manager.get_unprocessed_raw_activities()
            if not activities:
                logging.info("无未处理的活动数据")
                return stats
                
            stats["total"] = len(activities)
            logging.info(f"找到 {stats['total']} 条未处理活动")
            
            # 2. 遍历处理每条数据
            for idx, activity in enumerate(activities, 1):
                try:
                    # 执行分类
                    path_scores, top_2_paths = self.classify_text(
                        activity['raw_title'],
                        activity['raw_content']
                    )
                    
                    # 保存分类结果
                    save_success = db_manager.save_activity_result(
                        activity_raw_id=activity['id'],
                        title=activity['raw_title'],
                        content=activity['raw_content'],
                        publish_time=activity['raw_publish_time'],
                        source_type=activity['source_type'],
                        career_paths=path_scores,
                        top_2_paths=top_2_paths
                    )
                    
                    if save_success:
                        stats["success"] += 1
                        logging.info(f"成功处理第 {idx}/{stats['total']} 条活动：{activity['raw_title']}")
                    else:
                        stats["failed"] += 1
                        logging.error(f"保存失败 - 活动ID: {activity['id']}")
                    
                except Exception as e:
                    stats["failed"] += 1
                    logging.error(f"处理失败 - 活动ID: {activity['id']}, 错误: {str(e)}")
                    continue
                
                # 打印进度
                if idx % 10 == 0 or idx == stats["total"]:
                    print(f"处理进度: {idx}/{stats['total']}")
                    
        except Exception as e:
            logging.error(f"批量处理异常: {str(e)}")
            return stats
            
        # 3. 输出处理统计
        process_time = time.time() - start_time
        avg_time = process_time / stats["total"] if stats["total"] > 0 else 0
        
        summary = (
            f"\n批量处理完成:"
            f"\n- 总数量: {stats['total']} 条"
            f"\n- 成功: {stats['success']} 条"
            f"\n- 失败: {stats['failed']} 条"
            f"\n- 总耗时: {process_time:.2f} 秒"
            f"\n- 平均: {avg_time:.2f} 秒/条"
        )
        print(summary)
        logging.info(summary)
        
        return stats

# 全局分类器实例        
classifier = CareerPathClassifier()

def main():
    """批量处理入口函数"""
    try:
        print("开始批量处理活动分类...")
        # 使用全局分类器实例执行批量处理
        stats = classifier.batch_process()
        
        if stats["total"] == 0:
            print("当前无需处理的活动数据")
        elif stats["failed"] > 0:
            print(f"处理完成，但有 {stats['failed']} 条数据失败，请查看日志了解详情")
        else:
            print(f"所有 {stats['total']} 条数据处理成功")
            
    except Exception as e:
        print(f"批量处理出错: {str(e)}")
        logging.error(f"批量处理失败: {str(e)}")
    finally:
        # 关闭数据库连接
        db_manager.close()

# 测试代码
if __name__ == "__main__":
    # 测试文本
    test_title = "2025年考研复试调剂指导会通知"
    test_content = "为帮助考生顺利通过考研复试，学校将举办调剂指导会，讲解复试流程、专业课复习重点及调剂技巧。"
    print(f"=== 测试数据 ===\n标题：{test_title}\n内容：{test_content}\n")
    # 执行分类
    try:
        path_scores, top_2_paths = classifier.classify_text(test_title, test_content)
        
        # 3. 输出测试结果（
        print("=== 分类结果 ===")
        print("各生涯路径得分（降序）：")
        # 按得分降序排列
        sorted_scores = sorted(path_scores.items(), key=lambda x: x[1], reverse=True)
        for path, score in sorted_scores:
            print(f"  {path}: {score:.1f}分")
        print(f"\n得分最高的2个路径：{', '.join(top_2_paths)}")
        
    except Exception as e:
        print(f"测试失败：分类器调用异常 → {str(e)}")
        logging.error(f"分类器自测试失败：{str(e)}", exc_info=True)