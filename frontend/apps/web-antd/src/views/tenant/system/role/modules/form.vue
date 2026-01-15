<script lang="ts" setup>
/**
 * 租户角色新建/编辑表单抽屉（含权限选择器）
 * 遵循 vben-admin 规范
 */
import type { tenantApi } from '#/api';
import type { FormMode } from '#/composables';
import type { PermissionNode } from '#/components/business/permission-selector';

import { computed, nextTick, ref, watch } from 'vue';

import { useVbenDrawer } from '@vben/common-ui';

import { TreeSelect } from 'ant-design-vue';

import { useVbenForm } from '#/adapter/form';
import { tenantApi as tenant } from '#/api';
import { PermissionSelector } from '#/components/business/permission-selector';
import { $t } from '#/locales';

import { useFormSchema } from '../data';

type RoleInfo = tenantApi.TenantRoleInfo;

const emits = defineEmits<{
  success: [];
}>();

// 表单数据
const formData = ref<RoleInfo & { mode?: FormMode; parentId?: number }>();
const mode = ref<FormMode>('add');
const roleId = ref<number>();
const isEdit = computed(() => mode.value === 'edit');
const parentId = ref<null | number>(null);

// 父角色选择器
const roleList = ref<RoleInfo[]>([]);
const loadingRoles = ref(false);

// 权限选择器
const permissions = ref<PermissionNode[]>([]);
const filteredPermissions = ref<PermissionNode[]>([]);
const loadingPermissions = ref(false);
const selectedPermissionIds = ref<number[]>([]);
// 预留：继承权限（待后端 API 支持后启用）
// const inheritedPermissionIds = ref<number[]>([]);
// const inheritedFromMap = ref<Map<number, string>>(new Map());

// 基于父角色限制可选权限：缓存父角色的可用权限集合，避免重复请求
const parentPermCache = new Map<number, number[]>();

function filterPermissionsTree(nodes: PermissionNode[], allowed: Set<number>): PermissionNode[] {
  const result: PermissionNode[] = [];
  for (const n of nodes) {
    const children = n.children ? filterPermissionsTree(n.children, allowed) : undefined;
    if (allowed.has(n.id) || (children && children.length > 0)) {
      result.push({ ...n, children });
    }
  }
  return result;
}

async function getParentAllowedIds(pid: number): Promise<number[]> {
  if (!pid) return [];
  if (parentPermCache.has(pid)) return parentPermCache.get(pid)!;
  try {
    const detail = await tenant.getTenantRoleDetailApi(pid);
    const ids = (detail.permissionIds && detail.permissionIds.length > 0)
      ? [...detail.permissionIds]
      : (detail.permissions ? detail.permissions.map((p: any) => p.id) : []);
    parentPermCache.set(pid, ids);
    return ids;
  } catch {
    return [];
  }
}

async function updateFilteredPermissions() {
  // 未加载权限树时不处理
  if (!permissions.value || permissions.value.length === 0) {
    filteredPermissions.value = [];
    return;
  }
  // 无父角色：显示全部权限树
  if (!parentId.value) {
    filteredPermissions.value = permissions.value;
    return;
  }
  // 有父角色：仅显示父角色允许的权限子集
  const allowedIds = await getParentAllowedIds(parentId.value);
  const allowedSet = new Set<number>(allowedIds);
  filteredPermissions.value = filterPermissionsTree(permissions.value, allowedSet);
  // 清理已选中但不再允许的权限
  if (selectedPermissionIds.value.length) {
    selectedPermissionIds.value = selectedPermissionIds.value.filter((id) => allowedSet.has(id));
  }
}

watch([parentId, permissions], () => {
  void updateFilteredPermissions();
}, { immediate: true });

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
      const payload: any = {
        name: values.name,
        description: values.description || null,
        is_active: values.is_active ?? true,
        sort_order: values.sort_order ?? 0,
        permission_ids: selectedPermissionIds.value,
        parent_id: parentId.value,
      };
      if (values.code) payload.code = values.code;

      if (isEdit.value && roleId.value) {
        // 编辑模式（不传 code）
        await tenant.updateTenantRoleApi(
          roleId.value,
          {
            name: payload.name,
            description: payload.description,
            is_active: payload.is_active,
            sort_order: payload.sort_order,
            permission_ids: payload.permission_ids,
          },
          { showSuccessMessage: true, successMessage: $t('ui.actionMessage.updateSuccess') },
        );
      } else {
        // 新建模式
        await tenant.createTenantRoleApi(payload, {
          showSuccessMessage: true,
          successMessage: $t('ui.actionMessage.createSuccess'),
        });
      }
      emits('success');
      drawerApi.close();
    } catch {
      drawerApi.unlock();
    }
  },

  async onOpenChange(isOpen) {
    if (isOpen) {
      const data = drawerApi.getData<
        RoleInfo & { mode?: FormMode; parentId?: number }
      >();
      formData.value = data;
      mode.value = data?.mode ?? 'add';
      roleId.value = data?.id;
      parentId.value = data?.parentId ?? null;

      // 重置表单和权限选择
      await formApi.resetForm();
      selectedPermissionIds.value = [];

      // 加载角色列表（用于父角色选择）
      if (roleList.value.length === 0) {
        await loadRoleList();
      }

      // 加载权限树
      if (permissions.value.length === 0) {
        await loadPermissions();
      }

      // 根据父角色限制可选权限（若有）
      await updateFilteredPermissions();

      // 更新表单 schema（新增时不显示 code）
      formApi.setState({
        schema: useFormSchema(isEdit.value),
      });

      await nextTick();

      // 编辑模式：从详情接口获取完整数据
      if (isEdit.value && roleId.value) {
        try {
          const detail = await tenant.getTenantRoleDetailApi(roleId.value);
          parentId.value = detail.parentId ?? null;
          formApi.setValues({
            code: detail.code,
            name: detail.name,
            description: detail.description,
            is_active: detail.isActive,
            sort_order: detail.sortOrder,
            parent_id: detail.parentId,
          });
          // 优先使用 permissionIds（后端返回的 permission_ids）
          if (detail.permissionIds && detail.permissionIds.length > 0) {
            selectedPermissionIds.value = [...detail.permissionIds];
          } else if (detail.permissions && detail.permissions.length > 0) {
            // 兼容旧格式
            selectedPermissionIds.value = detail.permissions.map((p) => p.id);
          }
        } catch {
          // ignore
        }
      } else if (parentId.value) {
        // 新建模式且有父角色（从“添加子角色”进入）
        formApi.setValues({ parent_id: parentId.value });
      }
    }
  },
});

/**
 * 加载角色列表（用于父角色选择）
 */
async function loadRoleList() {
  loadingRoles.value = true;
  try {
    roleList.value = await tenant.getTenantRoleListApi();
  } catch {
    roleList.value = [];
  } finally {
    loadingRoles.value = false;
  }
}

/**
 * 获取可选的父角色列表（排除当前角色及其子角色）
 */
const parentRoleOptions = computed(() => {
  // 构建树形选项
  const buildTreeOptions = (roles: RoleInfo[], excludeId?: number): any[] => {
    return roles
      .filter((role) => role.id !== excludeId)
      .map((role) => ({
        value: role.id,
        label: role.name,
        children: role.children
          ? buildTreeOptions(role.children, excludeId)
          : undefined,
      }));
  };
  // 编辑时排除当前角色
  return buildTreeOptions(roleList.value, isEdit.value ? roleId.value : undefined);
});

/**
 * 加载权限树
 */
async function loadPermissions() {
  loadingPermissions.value = true;
  try {
    const rawPermissions = await tenant.getTenantPermissionTreeApi();
    // 转换为 PermissionSelector 需要的格式
    permissions.value = rawPermissions as PermissionNode[];
    // 初次加载后应用一次过滤
    await updateFilteredPermissions();
  } catch {
    permissions.value = [];
    filteredPermissions.value = [];
  } finally {
    loadingPermissions.value = false;
  }
}

/**
 * 抽屉标题
 */
const drawerTitle = computed(() => {
  return isEdit.value
    ? $t('tenant.system.role.edit')
    : $t('tenant.system.role.create');
});
</script>

<template>
  <Drawer :title="drawerTitle">
    <Form>
      <template #parent_id>
        <TreeSelect
          v-model:value="parentId"
          :tree-data="parentRoleOptions"
          :loading="loadingRoles"
          :placeholder="$t('tenant.system.role.placeholder.selectParent')"
          :allow-clear="true"
          :tree-default-expand-all="true"
          style="width: 100%"
        />
      </template>
      <template #permission_ids>
        <PermissionSelector
          v-model="selectedPermissionIds"
:permissions="filteredPermissions"
          :loading="loadingPermissions"
          :show-select-all="true"
          :default-expanded-level="2"
        />
      </template>
    </Form>
  </Drawer>
</template>
