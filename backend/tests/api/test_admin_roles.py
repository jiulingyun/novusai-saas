#!/usr/bin/env python3
"""
平台管理员角色 API 测试模块

测试 /admin/roles/* 接口
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


class TestAdminRoles(BaseAPITest):
    """平台管理员角色测试"""
    
    module_name = "平台角色管理 (/admin/roles)"
    
    def setup(self) -> None:
        """测试前登录"""
        self._do_login()
        # 生成唯一的测试角色代码
        self._test_data["role_code"] = f"test_role_{int(time.time())}"
    
    def teardown(self) -> None:
        """测试后清理"""
        # 尝试删除测试创建的角色
        role_id = self._test_data.get("created_role_id")
        if role_id:
            try:
                self.client.delete(f"/admin/roles/{role_id}")
            except Exception:
                pass
    
    def _run_tests(self) -> None:
        """运行所有测试"""
        # 1. 获取角色列表
        self.run_test("获取角色列表", self.test_list_roles)
        
        # 2. 创建角色
        self.run_test("创建角色", self.test_create_role)
        
        # 3. 创建角色 - 重复代码
        self.run_test("创建角色 - 重复代码", self.test_create_role_duplicate_code)
        
        # 4. 获取角色详情
        self.run_test("获取角色详情", self.test_get_role_detail)
        
        # 5. 获取角色详情 - 不存在
        self.run_test("获取角色详情 - 不存在", self.test_get_role_not_found)
        
        # 6. 更新角色
        self.run_test("更新角色", self.test_update_role)
        
        # 7. 分配角色权限
        self.run_test("分配角色权限", self.test_assign_permissions)
        
        # 8. 删除角色
        self.run_test("删除角色", self.test_delete_role)
        
        # 9. 删除角色 - 不存在
        self.run_test("删除角色 - 不存在", self.test_delete_role_not_found)
    
    def test_list_roles(self) -> None:
        """测试获取角色列表"""
        resp = self.client.get("/admin/roles")
        data = assert_success(resp, "获取角色列表失败")
        
        # 验证返回的是列表
        assert_true(isinstance(data["data"], list), "角色列表应为列表")
        
        # 如果有数据，验证结构
        if data["data"]:
            first_role = data["data"][0]
            assert_has_keys(first_role, ["id", "code", "name", "is_active"])
    
    def test_create_role(self) -> None:
        """测试创建角色"""
        role_code = self._test_data["role_code"]
        resp = self.client.post("/admin/roles", data={
            "code": role_code,
            "name": "测试角色",
            "description": "API测试创建的角色",
            "is_active": True,
            "sort_order": 100,
        })
        data = assert_success(resp, "创建角色失败")
        
        assert_has_keys(data["data"], ["id", "code", "name"])
        assert_equals(data["data"]["code"], role_code)
        
        # 保存角色ID供后续测试使用
        self._test_data["created_role_id"] = data["data"]["id"]
    
    def test_create_role_duplicate_code(self) -> None:
        """测试创建重复代码的角色"""
        role_code = self._test_data["role_code"]
        resp = self.client.post("/admin/roles", data={
            "code": role_code,
            "name": "重复角色",
            "description": "这个角色代码已存在",
        })
        assert_error(resp, 400, "应返回 400 错误")
    
    def test_get_role_detail(self) -> None:
        """测试获取角色详情"""
        role_id = self._test_data.get("created_role_id")
        if not role_id:
            raise AssertionError("没有可用的角色ID")
        
        resp = self.client.get(f"/admin/roles/{role_id}")
        data = assert_success(resp, "获取角色详情失败")
        
        assert_has_keys(data["data"], ["id", "code", "name", "permission_ids", "permission_codes"])
        assert_equals(data["data"]["id"], role_id)
    
    def test_get_role_not_found(self) -> None:
        """测试获取不存在的角色详情"""
        resp = self.client.get("/admin/roles/999999")
        assert_error(resp, 404, "应返回 404 错误")
    
    def test_update_role(self) -> None:
        """测试更新角色"""
        role_id = self._test_data.get("created_role_id")
        if not role_id:
            raise AssertionError("没有可用的角色ID")
        
        new_name = "更新后的测试角色"
        resp = self.client.put(f"/admin/roles/{role_id}", data={
            "name": new_name,
            "description": "已更新的描述",
        })
        data = assert_success(resp, "更新角色失败")
        assert_equals(data["data"]["name"], new_name)
    
    def test_assign_permissions(self) -> None:
        """测试分配角色权限"""
        role_id = self._test_data.get("created_role_id")
        if not role_id:
            raise AssertionError("没有可用的角色ID")
        
        # 先获取权限列表
        perm_resp = self.client.get("/admin/permissions/list")
        perm_data = perm_resp.json()
        
        # 取前几个权限ID
        perm_ids = [p["id"] for p in perm_data.get("data", [])[:3]]
        
        resp = self.client.put(f"/admin/roles/{role_id}/permissions", data={
            "permission_ids": perm_ids,
        })
        assert_success(resp, "分配权限失败")
        
        # 验证权限已分配
        detail_resp = self.client.get(f"/admin/roles/{role_id}")
        detail_data = detail_resp.json()
        assert_true(
            set(perm_ids).issubset(set(detail_data["data"]["permission_ids"])),
            "权限未正确分配"
        )
    
    def test_delete_role(self) -> None:
        """测试删除角色"""
        role_id = self._test_data.get("created_role_id")
        if not role_id:
            raise AssertionError("没有可用的角色ID")
        
        resp = self.client.delete(f"/admin/roles/{role_id}")
        assert_success(resp, "删除角色失败")
        
        # 验证已删除
        check_resp = self.client.get(f"/admin/roles/{role_id}")
        assert_error(check_resp, 404, "角色应已被删除")
        
        # 清除ID，避免 teardown 再次尝试删除
        del self._test_data["created_role_id"]
    
    def test_delete_role_not_found(self) -> None:
        """测试删除不存在的角色"""
        resp = self.client.delete("/admin/roles/999999")
        assert_error(resp, 404, "应返回 404 错误")
    
    def _do_login(self) -> None:
        """执行登录"""
        resp = self.client.post("/admin/auth/login", data={
            "username": config.ADMIN_USERNAME,
            "password": config.ADMIN_PASSWORD,
        })
        data = resp.json()
        self.client.set_token(data["data"]["access_token"])


if __name__ == "__main__":
    test = TestAdminRoles()
    report = test.run_all()
    report.print_summary()
