<script lang="ts" setup>
/**
 * 平台管理员列表页面
 * 遵循 vben-admin 规范
 */
import type {
  OnActionClickParams,
  VxeTableGridOptions,
} from '#/adapter/vxe-table';
import type { adminApi } from '#/api';

import { Page, useVbenDrawer, useVbenModal } from '@vben/common-ui';
import { IconifyIcon, Plus } from '@vben/icons';

import {
  Avatar,
  Badge,
  Button,
  Card,
  message,
  Modal,
  Tag,
  Tooltip,
} from 'ant-design-vue';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import { adminApi as admin } from '#/api';
import { $t } from '#/locales';
import { ADMIN_PERMISSIONS } from '#/utils/access';

import { useColumns, useGridFormSchema } from './data';
import Form from './modules/form.vue';
import ResetPasswordModal from './modules/reset-password-modal.vue';

type AdminInfo = adminApi.AdminInfo;

// 新建/编辑抽屉
const [FormDrawer, formDrawerApi] = useVbenDrawer({
  connectedComponent: Form,
  destroyOnClose: true,
});

// 重置密码弹窗
const [ResetPasswordModalComp, resetPasswordModalApi] = useVbenModal({
  connectedComponent: ResetPasswordModal,
  destroyOnClose: true,
});

// 表格
const [Grid, gridApi] = useVbenVxeGrid({
  formOptions: {
    schema: useGridFormSchema(),
    submitOnChange: true,
  },
  gridOptions: {
    columns: useColumns(onActionClick, onStatusChange),
    keepSource: true,
    pagerConfig: {
      enabled: true,
    },
    proxyConfig: {
      ajax: {
        query: async ({ page }, formValues) => {
          return await admin.getAdminListApi({
            page: page.currentPage,
            page_size: page.pageSize,
            ...formValues,
          });
        },
      },
    },
    cellConfig: {
      height: 64,
    },
    rowConfig: {
      keyField: 'id',
    },
    toolbarConfig: {
      custom: true,
      export: true,
      refresh: true,
      search: true,
      zoom: true,
    },
  } as VxeTableGridOptions<AdminInfo>,
});

/**
 * 操作按钮点击回调
 */
function onActionClick(e: OnActionClickParams<AdminInfo>) {
  switch (e.code) {
    case 'delete': {
      onDelete(e.row);
      break;
    }
    case 'edit': {
      onEdit(e.row);
      break;
    }
    case 'resetPassword': {
      onResetPassword(e.row);
      break;
    }
  }
}

/**
 * 状态切换回调
 */
async function onStatusChange(newStatus: boolean, row: AdminInfo) {
  const action = newStatus
    ? $t('admin.common.enable')
    : $t('admin.common.disable');
  try {
    await new Promise<void>((resolve, reject) => {
      Modal.confirm({
        content: $t('admin.system.admin.messages.toggleStatusConfirm', {
          action,
          name: row.username,
        }),
        onCancel: () => reject(new Error('cancelled')),
        onOk: () => resolve(),
        title: $t('admin.system.admin.messages.toggleStatusTitle'),
      });
    });
    await admin.toggleAdminStatusApi(row.id, { is_active: newStatus });
    message.success(`${action}${$t('ui.actionMessage.operationSuccess')}`);
    return true;
  } catch {
    return false;
  }
}

/**
 * 编辑
 */
function onEdit(row: AdminInfo) {
  formDrawerApi.setData({ ...row, isEdit: true }).open();
}

/**
 * 删除
 */
function onDelete(row: AdminInfo) {
  Modal.confirm({
    content: $t('admin.system.admin.messages.deleteConfirm', {
      name: row.username,
    }),
    okButtonProps: { danger: true },
    okText: $t('common.delete'),
    onOk: async () => {
      const hideLoading = message.loading({
        content: $t('admin.system.admin.messages.deleting', {
          name: row.username,
        }),
        duration: 0,
        key: 'delete_admin',
      });
      try {
        await admin.deleteAdminApi(row.id);
        message.success({
          content: $t('admin.system.admin.messages.deleteSuccess'),
          key: 'delete_admin',
        });
        onRefresh();
      } catch {
        hideLoading();
      }
    },
    title: $t('admin.system.admin.messages.deleteTitle'),
    type: 'warning',
  });
}

/**
 * 重置密码
 */
function onResetPassword(row: AdminInfo) {
  resetPasswordModalApi.setData(row).open();
}

/**
 * 刷新列表
 */
function onRefresh() {
  gridApi.query();
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
    <ResetPasswordModalComp @success="onRefresh" />

    <!-- 表格 -->
    <Grid>
        <template #toolbar-tools>
          <Button
            v-access:code="[ADMIN_PERMISSIONS.ADMIN_CREATE]"
            type="primary"
            @click="onCreate"
          >
            <Plus class="mr-1 size-4" />
            {{ $t('admin.system.admin.create') }}
          </Button>
        </template>

        <!-- 用户信息列：头像 + 用户名 + 邮箱 -->
        <template #user_info="{ row }">
          <div class="flex items-center gap-3">
            <Avatar
              :src="row.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${row.username}`"
              :size="40"
              class="shrink-0"
            />
            <div class="flex flex-col min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-medium text-gray-900 dark:text-gray-100 truncate">
                  {{ row.username }}
                </span>
                <span v-if="row.nickname" class="text-xs text-gray-400">
                  ({{ row.nickname }})
                </span>
              </div>
              <span class="text-xs text-gray-500 truncate">
                <IconifyIcon icon="lucide:mail" class="mr-1 inline-block text-gray-400" />
                {{ row.email }}
              </span>
            </div>
          </div>
        </template>

        <!-- 电话列 -->
        <template #phone_cell="{ row }">
          <div v-if="row.phone" class="flex items-center text-gray-600 dark:text-gray-400">
            <IconifyIcon icon="lucide:phone" class="mr-1.5 text-gray-400" />
            {{ row.phone }}
          </div>
          <span v-else class="text-gray-300">-</span>
        </template>

        <!-- 角色列 -->
        <template #role_cell="{ row }">
          <Tag v-if="row.roleName" color="processing" class="flex items-center gap-1 !m-0">
            <IconifyIcon icon="lucide:shield" class="text-xs" />
            {{ row.roleName }}
          </Tag>
          <Tag v-else color="default" class="!m-0">
            {{ $t('admin.common.notAssigned') }}
          </Tag>
        </template>

        <!-- 类型列 -->
        <template #type_cell="{ row }">
          <Tooltip v-if="row.isSuper" :title="$t('admin.system.admin.help.superAdminHelp')">
            <Badge status="error" />
            <span class="ml-1 text-red-500 font-medium">
              {{ $t('admin.system.admin.superAdmin') }}
            </span>
          </Tooltip>
          <span v-else class="text-gray-500">
            {{ $t('admin.system.admin.normalAdmin') }}
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
