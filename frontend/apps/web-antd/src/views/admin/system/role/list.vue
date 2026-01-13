<script lang="ts" setup>
/**
 * 平台角色列表页面
 * 遵循 vben-admin 规范
 */
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type { adminApi } from '#/api';

import { nextTick } from 'vue';

import { Page, useVbenDrawer } from '@vben/common-ui';
import { IconifyIcon, Plus } from '@vben/icons';

import { Button, message, Modal, Tag, Tooltip } from 'ant-design-vue';

import { useTableDragSort, useVbenVxeGrid } from '#/adapter/vxe-table';
import { adminApi as admin } from '#/api';
import { $t } from '#/locales';
import { ADMIN_PERMISSIONS } from '#/utils/access';

import { useColumns } from './data';
import Form from './modules/form.vue';

type RoleInfo = adminApi.RoleInfo;

// 新建/编辑抽屉
const [FormDrawer, formDrawerApi] = useVbenDrawer({
  connectedComponent: Form,
  destroyOnClose: true,
});

// 表格（角色列表不分页）
const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions: {
    columns: useColumns(onActionClick),
    height: 'auto',
    pagerConfig: {
      enabled: false,
    },
    proxyConfig: {
      ajax: {
        query: async () => {
          const roles = await admin.getRoleListApi();
          // 按 sortOrder 排序
          const sorted = [...roles].sort(
            (a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0),
          );
          // 查询完成后初始化拖拽
          nextTick(() => initDragSort());
          return { items: sorted, total: sorted.length };
        },
      },
    },
    rowConfig: {
      keyField: 'id',
    },
    toolbarConfig: {
      custom: true,
      refresh: true,
      search: true,
      zoom: true,
    },
  },
});

// 拖拽排序
const { initDragSort, refreshTable } = useTableDragSort(
  { get value() { return gridApi.grid; } },
  {
    sortField: 'sortOrder',
    onUpdate: (id, sortOrder) => admin.updateRoleApi(id as number, { sort_order: sortOrder }),
  },
);

/**
 * 操作按钮点击回调
 */
function onActionClick(e: OnActionClickParams<RoleInfo>) {
  switch (e.code) {
    case 'delete': {
      onDelete(e.row);
      break;
    }
    case 'edit': {
      onEdit(e.row);
      break;
    }
  }
}

/**
 * 编辑
 */
function onEdit(row: RoleInfo) {
  formDrawerApi.setData({ ...row, isEdit: true }).open();
}

/**
 * 删除
 */
function onDelete(row: RoleInfo) {
  Modal.confirm({
    content: $t('admin.system.role.messages.deleteConfirm', { name: row.name }),
    okButtonProps: { danger: true },
    okText: $t('common.delete'),
    onOk: async () => {
      const hideLoading = message.loading({
        content: $t('admin.system.role.messages.deleting', { name: row.name }),
        duration: 0,
        key: 'delete_role',
      });
      try {
        await admin.deleteRoleApi(row.id);
        message.success({
          content: $t('admin.system.role.messages.deleteSuccess'),
          key: 'delete_role',
        });
        onRefresh();
      } catch {
        hideLoading();
      }
    },
    title: $t('admin.system.role.messages.deleteTitle'),
    type: 'warning',
  });
}

/**
 * 刷新列表
 */
function onRefresh() {
  refreshTable();
}

/**
 * 新建
 */
function onCreate() {
  formDrawerApi.setData({ isEdit: false }).open();
}
</script>

<template>
  <Page auto-content-height>
    <FormDrawer @success="onRefresh" />

    <Grid>
      <template #toolbar-tools>
        <Button
          v-access:code="[ADMIN_PERMISSIONS.ROLE_CREATE]"
          type="primary"
          @click="onCreate"
        >
          <Plus class="mr-1 size-4" />
          {{ $t('admin.system.role.create') }}
        </Button>
      </template>

      <!-- 角色信息列 -->
      <template #role_info="{ row }">
        <div>
          <div class="font-medium">{{ row.name }}</div>
          <div class="text-xs text-gray-400 font-mono">{{ row.code }}</div>
        </div>
      </template>

      <!-- 描述列 -->
      <template #desc_cell="{ row }">
        <span v-if="row.description" class="text-gray-600 dark:text-gray-400">
          {{ row.description }}
        </span>
        <span v-else class="text-gray-300">-</span>
      </template>

      <!-- 权限数量列 -->
      <template #permissions_cell="{ row }">
        <Tooltip v-if="row.permissions && row.permissions.length > 0">
          <template #title>
            <div class="max-h-48 overflow-y-auto">
              <div v-for="perm in row.permissions" :key="perm.id" class="py-0.5">
                {{ perm.name }}
              </div>
            </div>
          </template>
          <Tag color="processing" class="!m-0">
            <IconifyIcon icon="lucide:key" class="mr-1" />
            {{ row.permissions.length }} {{ $t('admin.system.role.permissionCount') }}
          </Tag>
        </Tooltip>
        <Tag v-else color="warning" class="!m-0">
          <IconifyIcon icon="lucide:alert-circle" class="mr-1" />
          {{ $t('admin.system.role.noPermissions') }}
        </Tag>
      </template>

      <!-- 排序列 -->
      <template #sort_cell="{ row }">
        <span class="inline-flex items-center justify-center size-6 rounded bg-gray-100 dark:bg-gray-700 text-xs font-medium">
          {{ row.sortOrder ?? 0 }}
        </span>
      </template>

      <!-- 时间列 -->
      <template #time_cell="{ row }">
        <div v-if="row.createdAt" class="flex flex-col text-xs">
          <span class="text-gray-600 dark:text-gray-400">
            <IconifyIcon icon="lucide:calendar" class="mr-1 inline-block text-gray-400" />
            {{ new Date(row.createdAt).toLocaleDateString() }}
          </span>
          <span class="text-gray-400 ml-4">
            {{ new Date(row.createdAt).toLocaleTimeString() }}
          </span>
        </div>
        <span v-else class="text-gray-300">-</span>
      </template>
    </Grid>
  </Page>
</template>

<style>
/* Sortable 拖拽样式 - 不能用 scoped，否则不能应用到动态添加的元素 */
.sortable-ghost {
  opacity: 0.5;
  background: var(--ant-color-primary-bg) !important;
}

.sortable-ghost td {
  background: inherit !important;
}
</style>
