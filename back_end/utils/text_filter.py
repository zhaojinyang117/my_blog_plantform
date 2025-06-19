"""
文本内容过滤工具
用于过滤敏感词和不当内容
"""

import re
from typing import List, Tuple, Dict
from django.conf import settings


class SensitiveWordFilter:
    """
    敏感词过滤器
    采用简单的关键词匹配算法，支持替换和检测
    """
    
    # 默认敏感词列表（基础版本）
    DEFAULT_SENSITIVE_WORDS = [
        '垃圾内容', '广告', '刷屏', '色情', '暴力', 
        '政治敏感', '反动', '诈骗', '赌博', '毒品',
    ]
    
    def __init__(self, custom_words: List[str] = None):
        """
        初始化敏感词过滤器
        
        Args:
            custom_words: 自定义敏感词列表
        """
        self.sensitive_words = set(self.DEFAULT_SENSITIVE_WORDS)
        if custom_words:
            self.sensitive_words.update(custom_words)
            
        # 编译正则表达式模式
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译敏感词正则表达式模式"""
        # 按长度降序排列，优先匹配更长的词
        sorted_words = sorted(self.sensitive_words, key=len, reverse=True)
        
        # 转义特殊字符并构建模式
        escaped_words = [re.escape(word) for word in sorted_words]
        pattern = '|'.join(escaped_words)
        
        # 编译不区分大小写的模式
        self.pattern = re.compile(pattern, re.IGNORECASE) if pattern else None
        
    def add_words(self, words: List[str]):
        """
        添加敏感词
        
        Args:
            words: 要添加的敏感词列表
        """
        self.sensitive_words.update(words)
        self._compile_patterns()
    
    def remove_words(self, words: List[str]):
        """
        移除敏感词
        
        Args:
            words: 要移除的敏感词列表
        """
        self.sensitive_words.difference_update(words)
        self._compile_patterns()
    
    def contains_sensitive_words(self, text: str) -> bool:
        """
        检查文本是否包含敏感词
        
        Args:
            text: 要检查的文本
            
        Returns:
            bool: 是否包含敏感词
        """
        if not self.pattern or not text:
            return False
        return bool(self.pattern.search(text))
    
    def find_sensitive_words(self, text: str) -> List[str]:
        """
        查找文本中的所有敏感词
        
        Args:
            text: 要检查的文本
            
        Returns:
            List[str]: 找到的敏感词列表
        """
        if not self.pattern or not text:
            return []
        
        matches = self.pattern.findall(text)
        return list(set(matches))  # 去重
    
    def filter_text(self, text: str, replacement: str = '***') -> str:
        """
        过滤文本中的敏感词
        
        Args:
            text: 要过滤的文本
            replacement: 替换字符，默认为 '***'
            
        Returns:
            str: 过滤后的文本
        """
        if not self.pattern or not text:
            return text
        
        return self.pattern.sub(replacement, text)
    
    def get_filter_info(self, text: str) -> Dict:
        """
        获取文本过滤信息
        
        Args:
            text: 要分析的文本
            
        Returns:
            Dict: 包含是否包含敏感词、敏感词列表、过滤后文本等信息
        """
        result = {
            'has_sensitive_words': False,
            'sensitive_words': [],
            'filtered_text': text,
            'original_text': text
        }
        
        if self.contains_sensitive_words(text):
            result['has_sensitive_words'] = True
            result['sensitive_words'] = self.find_sensitive_words(text)
            result['filtered_text'] = self.filter_text(text)
        
        return result


class CommentContentFilter:
    """
    评论内容专用过滤器
    结合敏感词过滤和其他内容检查
    """
    
    def __init__(self):
        self.sensitive_word_filter = SensitiveWordFilter()
        
        # 其他规则
        self.max_length = getattr(settings, 'COMMENT_MAX_LENGTH', 1000)
        self.min_length = getattr(settings, 'COMMENT_MIN_LENGTH', 1)
        
        # 垃圾内容模式
        self.spam_patterns = [
            re.compile(r'(.)\1{4,}'),  # 连续相同字符
            re.compile(r'(http|www\.)', re.IGNORECASE),  # URL链接
            re.compile(r'[\u4e00-\u9fff]{0,2}[\w\s]*[\u4e00-\u9fff]{0,2}', re.IGNORECASE),  # 混合语言检查
        ]
    
    def check_content(self, content: str) -> Dict:
        """
        全面检查评论内容
        
        Args:
            content: 评论内容
            
        Returns:
            Dict: 检查结果
        """
        result = {
            'is_valid': True,
            'should_auto_approve': True,  # 是否应该自动审核通过
            'issues': [],
            'filtered_content': content,
            'original_content': content
        }
        
        # 基础验证
        if not content or not content.strip():
            result['is_valid'] = False
            result['issues'].append('评论内容不能为空')
            return result
            
        if len(content) < self.min_length:
            result['is_valid'] = False
            result['issues'].append(f'评论内容不能少于{self.min_length}个字符')
            
        if len(content) > self.max_length:
            result['is_valid'] = False
            result['issues'].append(f'评论内容不能超过{self.max_length}个字符')
        
        # 敏感词检查
        filter_info = self.sensitive_word_filter.get_filter_info(content)
        if filter_info['has_sensitive_words']:
            result['should_auto_approve'] = False
            result['issues'].append('包含敏感词，需要人工审核')
            result['filtered_content'] = filter_info['filtered_text']
        
        # 垃圾内容检查
        for pattern in self.spam_patterns[:1]:  # 只检查连续字符，简化版本
            if pattern.search(content):
                result['should_auto_approve'] = False
                result['issues'].append('可能包含垃圾内容，需要人工审核')
                break
        
        return result


# 全局过滤器实例
_comment_filter = None

def get_comment_filter() -> CommentContentFilter:
    """获取评论过滤器实例"""
    global _comment_filter
    if _comment_filter is None:
        _comment_filter = CommentContentFilter()
    return _comment_filter


def filter_comment_content(content: str) -> Dict:
    """
    快捷函数：过滤评论内容
    
    Args:
        content: 评论内容
        
    Returns:
        Dict: 过滤结果
    """
    return get_comment_filter().check_content(content)