"""
搜索工具模块
提供搜索相关的工具函数和类
"""

import re
from django.db.models import Q
from django.core.cache import cache
from django.conf import settings
import hashlib


class SearchQueryBuilder:
    """
    搜索查询构建器
    用于构建复杂的搜索查询条件
    """
    
    def __init__(self, model_class):
        self.model_class = model_class
        self.query_conditions = Q()
        
    def add_text_search(self, query, fields):
        """
        添加文本搜索条件
        
        Args:
            query (str): 搜索关键词
            fields (list): 要搜索的字段列表
        """
        if not query or not fields:
            return self
            
        # 清理搜索关键词
        cleaned_query = self._clean_query(query)
        if not cleaned_query:
            return self
            
        # 构建搜索条件
        text_conditions = Q()
        for field in fields:
            text_conditions |= Q(**{f"{field}__icontains": cleaned_query})
            
        self.query_conditions &= text_conditions
        return self
    
    def add_exact_match(self, field, value):
        """
        添加精确匹配条件
        
        Args:
            field (str): 字段名
            value: 匹配值
        """
        if value is not None:
            self.query_conditions &= Q(**{field: value})
        return self
    
    def add_range_filter(self, field, min_value=None, max_value=None):
        """
        添加范围过滤条件
        
        Args:
            field (str): 字段名
            min_value: 最小值
            max_value: 最大值
        """
        if min_value is not None:
            self.query_conditions &= Q(**{f"{field}__gte": min_value})
        if max_value is not None:
            self.query_conditions &= Q(**{f"{field}__lte": max_value})
        return self
    
    def build(self):
        """
        构建最终的查询条件
        
        Returns:
            Q: Django查询条件对象
        """
        return self.query_conditions
    
    def _clean_query(self, query):
        """
        清理搜索关键词
        
        Args:
            query (str): 原始搜索关键词
            
        Returns:
            str: 清理后的搜索关键词
        """
        if not query:
            return ""
            
        # 移除特殊字符，只保留字母、数字、中文和空格
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', query)
        
        # 移除多余的空格
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()


class SearchCache:
    """
    搜索缓存管理器
    """
    
    @staticmethod
    def get_cache_key(query, search_type, ordering, page, user_id=None):
        """
        生成搜索缓存键
        
        Args:
            query (str): 搜索关键词
            search_type (str): 搜索类型
            ordering (str): 排序方式
            page (str): 页码
            user_id (int, optional): 用户ID
            
        Returns:
            str: 缓存键
        """
        cache_key_parts = [
            f"{settings.CACHE_KEY_PREFIX}:search",
            f"q:{hashlib.md5(query.encode()).hexdigest()}",
            f"type:{search_type}",
            f"ordering:{ordering}",
            f"page:{page}"
        ]
        
        if user_id:
            cache_key_parts.append(f"user:{user_id}")
            
        return ":".join(cache_key_parts)
    
    @staticmethod
    def get_cached_result(cache_key):
        """
        获取缓存的搜索结果
        
        Args:
            cache_key (str): 缓存键
            
        Returns:
            dict or None: 缓存的搜索结果
        """
        return cache.get(cache_key)
    
    @staticmethod
    def cache_result(cache_key, result, timeout=None):
        """
        缓存搜索结果
        
        Args:
            cache_key (str): 缓存键
            result (dict): 搜索结果
            timeout (int, optional): 缓存超时时间（秒）
        """
        if timeout is None:
            timeout = settings.CACHE_TIMEOUT.get('search_results', 300)
        
        cache.set(cache_key, result, timeout=timeout)


class SearchHighlighter:
    """
    搜索结果高亮器
    """
    
    @staticmethod
    def highlight_text(text, query, max_length=200):
        """
        在文本中高亮搜索关键词
        
        Args:
            text (str): 原始文本
            query (str): 搜索关键词
            max_length (int): 最大文本长度
            
        Returns:
            str: 高亮后的文本
        """
        if not text or not query:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # 清理搜索关键词
        cleaned_query = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', query)
        keywords = cleaned_query.split()
        
        if not keywords:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # 查找关键词在文本中的位置
        highlighted_text = text
        for keyword in keywords:
            if keyword:
                # 使用正则表达式进行不区分大小写的替换
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                highlighted_text = pattern.sub(
                    f'<mark>{keyword}</mark>', 
                    highlighted_text
                )
        
        # 截取文本长度
        if len(highlighted_text) > max_length:
            # 尝试在关键词附近截取
            mark_pos = highlighted_text.find('<mark>')
            if mark_pos != -1:
                start = max(0, mark_pos - max_length // 2)
                end = start + max_length
                highlighted_text = highlighted_text[start:end]
                if start > 0:
                    highlighted_text = "..." + highlighted_text
                if end < len(text):
                    highlighted_text = highlighted_text + "..."
            else:
                highlighted_text = highlighted_text[:max_length] + "..."
        
        return highlighted_text


def validate_search_params(query, search_type, ordering):
    """
    验证搜索参数
    
    Args:
        query (str): 搜索关键词
        search_type (str): 搜索类型
        ordering (str): 排序方式
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # 验证搜索关键词
    if not query or len(query.strip()) < 1:
        return False, "搜索关键词不能为空"
    
    if len(query) > 100:
        return False, "搜索关键词过长"
    
    # 验证搜索类型
    valid_search_types = ['all', 'title', 'content', 'author']
    if search_type not in valid_search_types:
        return False, f"无效的搜索类型，支持的类型：{', '.join(valid_search_types)}"
    
    # 验证排序方式
    valid_orderings = ['-created_at', 'created_at', '-view_count', 'view_count', 'title', '-title']
    if ordering not in valid_orderings:
        return False, f"无效的排序方式，支持的排序：{', '.join(valid_orderings)}"
    
    return True, ""
