"""
数据遮蔽功能测试

测试数据遮蔽处理器的各种场景。

许可声明:
本插件是基于 Baserow 开源 API 独立开发的扩展功能,
完全独立编写,未复制任何非开源代码,遵循 MIT 许可证发布。
"""

import pytest

from access_control.data_masking_handler import (
    MASK_SYMBOL,
    mask_row_data,
    _mask_value,
    _get_strictest_permission,
)


class TestMaskValue:
    """测试 _mask_value 函数"""
    
    def test_mask_none(self):
        """测试遮蔽 None 值"""
        assert _mask_value(None) == MASK_SYMBOL
    
    def test_mask_string(self):
        """测试遮蔽字符串"""
        assert _mask_value("hello") == MASK_SYMBOL
    
    def test_mask_number(self):
        """测试遮蔽数字"""
        assert _mask_value(123) == MASK_SYMBOL
        assert _mask_value(3.14) == MASK_SYMBOL
    
    def test_mask_bool(self):
        """测试遮蔽布尔值"""
        assert _mask_value(True) == MASK_SYMBOL
        assert _mask_value(False) == MASK_SYMBOL
    
    def test_mask_list(self):
        """测试遮蔽列表"""
        assert _mask_value([1, 2, 3]) == [MASK_SYMBOL]
    
    def test_mask_dict(self):
        """测试遮蔽字典"""
        result = _mask_value({"key": "value"})
        assert result == {"masked": True, "value": MASK_SYMBOL}


class TestMaskRowData:
    """测试 mask_row_data 函数"""
    
    def test_mask_entire_row(self):
        """测试整行遮蔽"""
        row_data = {
            "id": 1,
            "order": "1.00000",
            "field_1": "name",
            "field_2": 100,
            "field_3": ["a", "b"],
        }
        
        result = mask_row_data(row_data, set(), mask_entire_row=True)
        
        # id 和 order 应该保留
        assert result["id"] == 1
        assert result["order"] == "1.00000"
        # 其他字段应该被遮蔽
        assert result["field_1"] == MASK_SYMBOL
        assert result["field_2"] == MASK_SYMBOL
        assert result["field_3"] == [MASK_SYMBOL]
    
    def test_mask_specific_fields(self):
        """测试遮蔽特定字段"""
        row_data = {
            "id": 1,
            "order": "1.00000",
            "field_1": "name",
            "field_2": 100,
            "field_3": "visible",
        }
        
        # 只遮蔽 field_1 和 field_2
        result = mask_row_data(row_data, {1, 2}, mask_entire_row=False)
        
        assert result["id"] == 1
        assert result["order"] == "1.00000"
        assert result["field_1"] == MASK_SYMBOL
        assert result["field_2"] == MASK_SYMBOL
        assert result["field_3"] == "visible"  # 不遮蔽
    
    def test_mask_with_user_field_names(self):
        """测试使用用户字段名称时的遮蔽"""
        row_data = {
            "id": 1,
            "order": "1.00000",
            "Name": "John",
            "Age": 30,
            "Email": "john@example.com",
        }
        
        # 字段ID到名称的映射
        field_id_to_name = {1: "Name", 2: "Age"}
        
        # 遮蔽 field_1 (Name) 和 field_2 (Age)
        result = mask_row_data(row_data, {1, 2}, mask_entire_row=False, field_id_to_name=field_id_to_name)
        
        assert result["id"] == 1
        assert result["order"] == "1.00000"
        assert result["Name"] == MASK_SYMBOL
        assert result["Age"] == MASK_SYMBOL
        assert result["Email"] == "john@example.com"  # 不遮蔽
    
    def test_no_masking(self):
        """测试不需要遮蔽的情况"""
        row_data = {
            "id": 1,
            "order": "1.00000",
            "field_1": "name",
            "field_2": 100,
        }
        
        result = mask_row_data(row_data, set(), mask_entire_row=False)
        
        # 所有字段都应该保持原样
        assert result == row_data


class TestGetStrictestPermission:
    """测试 _get_strictest_permission 函数"""
    
    def test_single_permission(self):
        """测试单个权限"""
        assert _get_strictest_permission(["editable"]) == "editable"
        assert _get_strictest_permission(["read_only"]) == "read_only"
        assert _get_strictest_permission(["invisible"]) == "invisible"
    
    def test_multiple_permissions(self):
        """测试多个权限取最严格"""
        assert _get_strictest_permission(["editable", "read_only"]) == "read_only"
        assert _get_strictest_permission(["editable", "invisible"]) == "invisible"
        assert _get_strictest_permission(["read_only", "invisible"]) == "invisible"
        assert _get_strictest_permission(["editable", "read_only", "invisible"]) == "invisible"
    
    def test_empty_permissions(self):
        """测试空权限列表"""
        assert _get_strictest_permission([]) == "editable"

