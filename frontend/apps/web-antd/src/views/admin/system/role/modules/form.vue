<script lang="ts" setup>
/**
 * 平台角色新建/编辑表单抽屉（含权限树）
 * 遵循 vben-admin 规范
 */
import type { adminApi } from '#/api';

import { computed, nextTick, ref } from 'vue';

import { Tree, useVbenDrawer } from '@vben/common-ui';

import { Spin } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { adminApi as admin } from '#/api';
import { $t } from '#/locales';

type PermissionNode = adminApi.PermissionNode;
type RoleInfo = adminApi.RoleInfo;

import { useFormSchema } from '../data';

const emits = defineEmits<{
  success: [];
}>();

// 表单数据
const formData = ref<RoleInfo & { isEdit?: boolean }>();
const isEdit = ref(false);
const roleId = ref<number>();

// 权限树
const permissions = ref<PermissionNode[]>([]);
const loadingPermissions = ref(false);
const selectedPermissionIds = ref<number[]>([]);

// 表单
const [Form, formApi] = useVbenForm({
  schema: useFormSchema(false),
  showDefaultActions: false,
});

// 抽屉
const [Drawer, drawerApi] = useVbenDrawer({
  async onConfirm() {
    const { valid } = await formApi.validate();
    if (!valid) return;

    const values = await formApi.getValues();
    drawerApi.lock();

    try {
      const payload = {
        code: values.code,
        name: values.name,
        description: values.description || null,
        is_active: values.is_active ?? true,
        sort_order: values.sort_order ?? 0,
        permission_ids: selectedPermissionIds.value,
      };

      if (isEdit.value && roleId.value) {
        // 编辑模式（不传 code）
        await admin.updateRoleApi(roleId.value, {
          name: payload.name,
          description: payload.description,
          is_active: payload.is_active,
          sort_order: payload.sort_order,
          permission_ids: payload.permission_ids,
        });
      } else {
        // 新建模式
        await admin.createRoleApi(payload);
      }
      emits('success');
      drawerApi.close();
    } catch {
      drawerApi.unlock();
    }
  },

  async onOpenChange(isOpen) {
    if (isOpen) {
      const data = drawerApi.getData<RoleInfo & { isEdit?: boolean }>();
      formData.value = data;
      isEdit.value = data?.isEdit ?? false;
      roleId.value = data?.id;

      // 重置表单和权限选择
      await formApi.resetForm();
      selectedPermissionIds.value = [];

      // 加载权限树
      if (permissions.value.length === 0) {
        await loadPermissions();
      }

      // 更新表单 schema
      formApi.setState({
        schema: useFormSchema(isEdit.value),
      });

      await nextTick();

      // 编辑模式时填充数据
      if (data && isEdit.value) {
        formApi.setValues({
          code: data.code,
          name: data.name,
          description: data.description,
          is_active: data.isActive,
          sort_order: data.sortOrder,
        });
        // 回显已选权限
        if (data.permissions) {
          selectedPermissionIds.value = data.permissions.map((p) => p.id);
        }
      }
    }
  },
});

/**
 * 加载权限树
 */
async function loadPermissions() {
  loadingPermissions.value = true;
  try {
    permissions.value = await admin.getPermissionTreeApi();
  } catch {
    permissions.value = [];
  } finally {
    loadingPermissions.value = false;
  }
}

/**
 * 转换权限树为 Tree 组件需要的格式
 */
function transformTreeData(nodes: PermissionNode[]): any[] {
  return nodes.map((node) => ({
    key: node.id,
    title: node.name,
    value: node.id,
    children: node.children ? transformTreeData(node.children) : undefined,
  }));
}

/**
 * 抽屉标题
 */
const drawerTitle = computed(() => {
  return isEdit.value
    ? $t('admin.system.role.edit')
    : $t('admin.system.role.create');
});

/**
 * Tree 数据
 */
const treeData = computed(() => transformTreeData(permissions.value));
</script>

<template>
  <Drawer :title="drawerTitle">
    <Form>
      <template #permission_ids="slotProps">
        <Spin :spinning="loadingPermissions" wrapper-class-name="w-full">
          <Tree
            v-model:modelValue="selectedPermissionIds"
            :tree-data="treeData"
            checkable
            bordered
            :default-expanded-level="2"
            v-bind="slotProps"
            value-field="value"
            label-field="title"
          />
        </Spin>
      </template>
    </Form>
  </Drawer>
</template>
