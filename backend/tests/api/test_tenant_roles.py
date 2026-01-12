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
    """租户角色管理测试"""
    
    module_name = "租户角色管理 (/tenant/roles)"
    
    def setup(self) -> None:
        """测试前登录"""
        if config.TENANT_ADMIN_USERNAME and config.TENANT_ADMIN_PASSWORD:
            self._do_login()
            # 生成唯一的测试角色代码
            self._test_data["role_code"] = f"test_role_{int(time.time())}"
    
    def teardown(self) -> None:
        """测试后清理"""
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
        
        # 7. 删除角色
        self.run_test("删除角色", self.test_delete_role, skip_reason)
    
    def test_list_roles(self) -> None:
        """测试获取角色列表"""
        resp = self.client.get("/tenant/roles")
        data = assert_success(resp, "获取角色列表失败")
        
        assert_true(isinstance(data["data"], list), "角色列表应为列表")
    
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
        
        assert_has_keys(data["data"], ["id", "code", "name", "permission_ids", "permission_codes"])
    
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
