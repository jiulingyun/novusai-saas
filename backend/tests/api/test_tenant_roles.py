#!/usr/bin/env python3
"""
租户角色管理 API 测试模块

测试 /tenant/roles/* 接口

注意：需要先配置租户管理员账号才能运行此测试
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.api.base import (
    BaseAPITest,
    assert_success,
    assert_error,
    assert_has_keys,
    assert_true,
    assert_equals,
    config,
)


class TestTenantRoles(BaseAPITest):
    """租户角色管理测试（含多级角色功能）"""
    
    module_name = "租户角色管理 (/tenant/roles)"
    
    def setup(self) -> None:
        """测试前登录"""
        if config.TENANT_ADMIN_USERNAME and config.TENANT_ADMIN_PASSWORD:
            self._do_login()
            # 生成唯一的测试角色代码
            ts = int(time.time())
            self._test_data["role_code"] = f"test_role_{ts}"
            self._test_data["child_role_code"] = f"test_child_{ts}"
            self._test_data["grandchild_role_code"] = f"test_grandchild_{ts}"
    
    def teardown(self) -> None:
        """测试后清理（从叶子节点开始删除）"""
        # 先删除孙角色
        grandchild_id = self._test_data.get("grandchild_role_id")
        if grandchild_id:
            try:
                self.client.delete(f"/tenant/roles/{grandchild_id}")
            except Exception:
                pass
        
        # 再删除子角色
        child_id = self._test_data.get("child_role_id")
        if child_id:
            try:
                self.client.delete(f"/tenant/roles/{child_id}")
            except Exception:
                pass
        
        # 最后删除父角色
        role_id = self._test_data.get("created_role_id")
        if role_id:
            try:
                self.client.delete(f"/tenant/roles/{role_id}")
            except Exception:
                pass
    
    def _run_tests(self) -> None:
        """运行所有测试"""
        skip_reason = None
        if not config.TENANT_ADMIN_USERNAME or not config.TENANT_ADMIN_PASSWORD:
            skip_reason = "未配置租户管理员账号"
        
        # ========== 基础测试 ==========
        # 1. 获取角色列表
        self.run_test("获取角色列表", self.test_list_roles, skip_reason)
        
        # 2. 创建角色
        self.run_test("创建角色", self.test_create_role, skip_reason)
        
        # 3. 创建角色 - 重复代码
        self.run_test("创建角色 - 重复代码", self.test_create_role_duplicate_code, skip_reason)
        
        # 4. 获取角色详情
        self.run_test("获取角色详情", self.test_get_role_detail, skip_reason)
        
        # 5. 更新角色
        self.run_test("更新角色", self.test_update_role, skip_reason)
        
        # 6. 分配角色权限
        self.run_test("分配角色权限", self.test_assign_permissions, skip_reason)
        
        # ========== 多级角色测试 ==========
        # 7. 获取角色树
        self.run_test("获取角色树", self.test_get_role_tree, skip_reason)
        
        # 8. 创建子角色
        self.run_test("创建子角色", self.test_create_child_role, skip_reason)
        
        # 9. 创建孙角色（多层级）
        self.run_test("创建孙角色", self.test_create_grandchild_role, skip_reason)
        
        # 10. 获取子角色列表
        self.run_test("获取子角色列表", self.test_get_children, skip_reason)
        
        # 11. 获取有效权限（继承）
        self.run_test("获取有效权限", self.test_get_effective_permissions, skip_reason)
        
        # 12. 移动角色节点
        self.run_test("移动角色节点", self.test_move_role, skip_reason)
        
        # 13. 循环引用检测
        self.run_test("循环引用检测", self.test_circular_reference, skip_reason)
        
        # 14. 删除有子角色的角色 - 应失败
        self.run_test("删除有子角色的角色 - 应失败", self.test_delete_role_with_children, skip_reason)
        
        # ========== 清理测试 ==========
        # 15. 删除孙角色
        self.run_test("删除孙角色", self.test_delete_grandchild_role, skip_reason)
        
        # 16. 删除子角色
        self.run_test("删除子角色", self.test_delete_child_role, skip_reason)
        
        # 17. 删除角色
        self.run_test("删除角色", self.test_delete_role, skip_reason)
    
    def test_list_roles(self) -> None:
        """测试获取角色列表"""
        resp = self.client.get("/tenant/roles")
        data = assert_success(resp, "获取角色列表失败")
        
        assert_true(isinstance(data["data"], list), "角色列表应为列表")
        
        # 如果有数据，验证结构（含新增的层级字段）
        if data["data"]:
            first_role = data["data"][0]
            assert_has_keys(first_role, ["id", "code", "name", "is_active", "parent_id", "level"])
    
    def test_create_role(self) -> None:
        """测试创建角色"""
        role_code = self._test_data["role_code"]
        resp = self.client.post("/tenant/roles", data={
            "code": role_code,
            "name": "测试角色",
            "description": "租户内测试角色",
            "is_active": True,
            "sort_order": 100,
        })
        data = assert_success(resp, "创建角色失败")
        
        assert_has_keys(data["data"], ["id", "code", "name", "tenant_id"])
        assert_equals(data["data"]["code"], role_code)
        
        self._test_data["created_role_id"] = data["data"]["id"]
    
    def test_create_role_duplicate_code(self) -> None:
        """测试创建重复代码的角色"""
        role_code = self._test_data["role_code"]
        resp = self.client.post("/tenant/roles", data={
            "code": role_code,
            "name": "重复角色",
        })
        assert_error(resp, 400, "应返回 400 错误")
    
    def test_get_role_detail(self) -> None:
        """测试获取角色详情"""
        role_id = self._test_data.get("created_role_id")
        if not role_id:
            raise AssertionError("没有可用的角色ID")
        
        resp = self.client.get(f"/tenant/roles/{role_id}")
        data = assert_success(resp, "获取角色详情失败")
        
        # 验证基础字段和新增的层级字段
        assert_has_keys(data["data"], [
            "id", "code", "name", "permission_ids", "permission_codes",
            "parent_id", "path", "level", "children_count", "has_children"
        ])
        assert_equals(data["data"]["id"], role_id)
        # 根角色的 parent_id 应为 None
        assert_equals(data["data"]["parent_id"], None)
        assert_equals(data["data"]["level"], 1)
    
    def test_update_role(self) -> None:
        """测试更新角色"""
        role_id = self._test_data.get("created_role_id")
        if not role_id:
            raise AssertionError("没有可用的角色ID")
        
        new_name = "更新后的角色名"
        resp = self.client.put(f"/tenant/roles/{role_id}", data={
            "name": new_name,
        })
        data = assert_success(resp, "更新角色失败")
        assert_equals(data["data"]["name"], new_name)
    
    def test_assign_permissions(self) -> None:
        """测试分配角色权限"""
        role_id = self._test_data.get("created_role_id")
        if not role_id:
            raise AssertionError("没有可用的角色ID")
        
        # 获取租户端权限
        perm_resp = self.client.get("/tenant/permissions/list")
        perm_data = perm_resp.json()
        
        perm_ids = [p["id"] for p in perm_data.get("data", [])[:3]]
        
        resp = self.client.put(f"/tenant/roles/{role_id}/permissions", data={
            "permission_ids": perm_ids,
        })
        assert_success(resp, "分配权限失败")
    
    def test_delete_role(self) -> None:
        """测试删除角色"""
        role_id = self._test_data.get("created_role_id")
        if not role_id:
            raise AssertionError("没有可用的角色ID")
        
        resp = self.client.delete(f"/tenant/roles/{role_id}")
        assert_success(resp, "删除角色失败")
        
        # 验证已删除
        check_resp = self.client.get(f"/tenant/roles/{role_id}")
        assert_error(check_resp, 404, "角色应已被删除")
        
        del self._test_data["created_role_id"]
    
    # ========== 多级角色测试方法 ==========
    
    def test_get_role_tree(self) -> None:
        """测试获取角色树"""
        resp = self.client.get("/tenant/roles/tree")
        data = assert_success(resp, "获取角色树失败")
        
        # 验证返回的是列表（树节点列表）
        assert_true(isinstance(data["data"], list), "角色树应为列表")
    
    def test_create_child_role(self) -> None:
        """测试创建子角色"""
        parent_id = self._test_data.get("created_role_id")
        if not parent_id:
            raise AssertionError("没有可用的父角色ID")
        
        child_code = self._test_data["child_role_code"]
        resp = self.client.post("/tenant/roles", data={
            "code": child_code,
            "name": "测试子角色",
            "description": "父角色下的子角色",
            "is_active": True,
            "parent_id": parent_id,
        })
        data = assert_success(resp, "创建子角色失败")
        
        # 验证父子关系
        assert_equals(data["data"]["parent_id"], parent_id)
        assert_equals(data["data"]["level"], 2)  # 子角色是第二层
        
        self._test_data["child_role_id"] = data["data"]["id"]
    
    def test_create_grandchild_role(self) -> None:
        """测试创建孙角色（多层级）"""
        parent_id = self._test_data.get("child_role_id")
        if not parent_id:
            raise AssertionError("没有可用的子角色ID")
        
        grandchild_code = self._test_data["grandchild_role_code"]
        resp = self.client.post("/tenant/roles", data={
            "code": grandchild_code,
            "name": "测试孙角色",
            "description": "子角色下的孙角色",
            "is_active": True,
            "parent_id": parent_id,
        })
        data = assert_success(resp, "创建孙角色失败")
        
        # 验证父子关系
        assert_equals(data["data"]["parent_id"], parent_id)
        assert_equals(data["data"]["level"], 3)  # 孙角色是第三层
        
        self._test_data["grandchild_role_id"] = data["data"]["id"]
    
    def test_get_children(self) -> None:
        """测试获取子角色列表"""
        parent_id = self._test_data.get("created_role_id")
        if not parent_id:
            raise AssertionError("没有可用的父角色ID")
        
        resp = self.client.get(f"/tenant/roles/{parent_id}/children")
        data = assert_success(resp, "获取子角色列表失败")
        
        # 验证返回的是列表
        assert_true(isinstance(data["data"], list), "子角色列表应为列表")
        # 应该有一个子角色
        assert_true(len(data["data"]) >= 1, "应该至少有一个子角色")
        
        # 验证子角色的 parent_id
        for child in data["data"]:
            assert_equals(child["parent_id"], parent_id)
    
    def test_get_effective_permissions(self) -> None:
        """测试获取有效权限（含继承）"""
        child_id = self._test_data.get("child_role_id")
        if not child_id:
            raise AssertionError("没有可用的子角色ID")
        
        resp = self.client.get(f"/tenant/roles/{child_id}/permissions/effective")
        data = assert_success(resp, "获取有效权限失败")
        
        # 验证返回的是列表
        assert_true(isinstance(data["data"], list), "有效权限应为列表")
    
    def test_move_role(self) -> None:
        """测试移动角色节点"""
        grandchild_id = self._test_data.get("grandchild_role_id")
        parent_id = self._test_data.get("created_role_id")
        if not grandchild_id or not parent_id:
            raise AssertionError("没有可用的角色ID")
        
        # 将孙角色移动到根角色下（从第3层移动到第2层）
        resp = self.client.put(f"/tenant/roles/{grandchild_id}/move", data={
            "new_parent_id": parent_id,
        })
        data = assert_success(resp, "移动角色失败")
        
        # 验证移动后的父角色和层级
        assert_equals(data["data"]["parent_id"], parent_id)
        assert_equals(data["data"]["level"], 2)
        
        # 移动回原位置（回到子角色下）
        child_id = self._test_data.get("child_role_id")
        resp = self.client.put(f"/tenant/roles/{grandchild_id}/move", data={
            "new_parent_id": child_id,
        })
        data = assert_success(resp, "移动角色回原位置失败")
        assert_equals(data["data"]["level"], 3)
    
    def test_circular_reference(self) -> None:
        """测试循环引用检测"""
        parent_id = self._test_data.get("created_role_id")
        child_id = self._test_data.get("child_role_id")
        if not parent_id or not child_id:
            raise AssertionError("没有可用的角色ID")
        
        # 尝试将父角色移动到子角色下（应该失败）
        resp = self.client.put(f"/tenant/roles/{parent_id}/move", data={
            "new_parent_id": child_id,
        })
        assert_error(resp, 400, "循环引用应返回 400 错误")
    
    def test_delete_role_with_children(self) -> None:
        """测试删除有子角色的角色 - 应失败"""
        parent_id = self._test_data.get("created_role_id")
        if not parent_id:
            raise AssertionError("没有可用的父角色ID")
        
        resp = self.client.delete(f"/tenant/roles/{parent_id}")
        assert_error(resp, 400, "删除有子角色的角色应返回 400 错误")
    
    def test_delete_grandchild_role(self) -> None:
        """测试删除孙角色"""
        grandchild_id = self._test_data.get("grandchild_role_id")
        if not grandchild_id:
            raise AssertionError("没有可用的孙角色ID")
        
        resp = self.client.delete(f"/tenant/roles/{grandchild_id}")
        assert_success(resp, "删除孙角色失败")
        
        del self._test_data["grandchild_role_id"]
    
    def test_delete_child_role(self) -> None:
        """测试删除子角色"""
        child_id = self._test_data.get("child_role_id")
        if not child_id:
            raise AssertionError("没有可用的子角色ID")
        
        resp = self.client.delete(f"/tenant/roles/{child_id}")
        assert_success(resp, "删除子角色失败")
        
        del self._test_data["child_role_id"]
    
    def _do_login(self) -> None:
        """执行登录"""
        resp = self.client.post("/tenant/auth/login", data={
            "username": config.TENANT_ADMIN_USERNAME,
            "password": config.TENANT_ADMIN_PASSWORD,
        })
        data = resp.json()
        self.client.set_token(data["data"]["access_token"])


if __name__ == "__main__":
    test = TestTenantRoles()
    report = test.run_all()
    report.print_summary()
