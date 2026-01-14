<script lang="ts" setup>
/**
 * 平台管理员列表页面
 */
import type { OnActionClickParams, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { adminApi } from '#/api';

import { Page, useVbenDrawer, useVbenModal } from '@vben/common-ui';
import { IconifyIcon, Plus } from '@vben/icons';

import { Avatar, Badge, Button, Tag, Tooltip } from 'ant-design-vue';

import {
  useGridSearchFormOptions,
  useVbenVxeGrid,
} from '#/adapter/vxe-table';
import { adminApi as admin } from '#/api';
import { useCrudActions } from '#/composables';
import { formatDateOnly, formatTimeOnly } from '#/utils/common';

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

// CRUD 操作引用（用于函数提前引用）
let crud: ReturnType<typeof useCrudActions<AdminInfo>>;

/** 操作按钮点击 */
function onActionClick(e: OnActionClickParams<AdminInfo>) {
  switch (e.code) {
    case 'delete': { crud.onDelete(e.row); break; }
    case 'edit': { crud.onEdit(e.row); break; }
    case 'resetPassword': { resetPasswordModalApi.setData(e.row).open(); break; }
  }
}

/** 状态切换 */
function handleToggleStatus(newStatus: boolean, row: AdminInfo) {
  return crud.onToggleStatus(newStatus, row);
}

// 表格
const [Grid, gridApi] = useVbenVxeGrid({
  formOptions: useGridSearchFormOptions(useGridFormSchema()),
  gridOptions: {
    columns: useColumns<AdminInfo>(onActionClick, handleToggleStatus),
    keepSource: true,
    pagerConfig: { enabled: true },
    proxyConfig: {
      ajax: {
        query: async ({ page }, formValues) => {
          return await admin.getAdminListApi({
            ...formValues,
            'page[number]': page.currentPage,
            'page[size]': page.pageSize,
            'sort': '-created_at',
          });
        },
      },
    },
    cellConfig: { height: 64 },
    rowConfig: { keyField: 'id' },
    toolbarConfig: { custom: true, export: true, refresh: true, search: true, zoom: true },
  } as VxeTableGridOptions<AdminInfo>,
});

// CRUD 操作
crud = useCrudActions<AdminInfo>({
  gridApi,
  formDrawerApi,
  deleteApi: admin.deleteAdminApi,
  toggleStatusApi: admin.toggleAdminStatusApi,
  i18nPrefix: 'admin.system.admin',
  nameField: 'username',
});

const { onCreate, onRefresh } = crud;
</script>

<template>
  <Page auto-content-height>
    <FormDrawer @success="onRefresh" />
    <ResetPasswordModalComp @success="onRefresh" />

    <!-- 表格 -->
    <Grid>
      <template #toolbar-tools>
        <Button
          v-access:code="['admin_user:create']"
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
            :src="
              row.avatar ||
              `https://api.dicebear.com/7.x/avataaars/svg?seed=${row.username}`
            "
            :size="40"
            class="shrink-0"
          />
          <div class="flex min-w-0 flex-col">
            <div class="flex items-center gap-2">
              <span
                class="truncate font-medium text-gray-900 dark:text-gray-100"
              >
                {{ row.username }}
              </span>
              <span v-if="row.nickname" class="text-xs text-gray-400">
                ({{ row.nickname }})
              </span>
            </div>
            <span class="truncate text-xs text-gray-500">
              <IconifyIcon
                icon="lucide:mail"
                class="mr-1 inline-block text-gray-400"
              />
              {{ row.email }}
            </span>
          </div>
        </div>
      </template>

      <!-- 电话列 -->
      <template #phone_cell="{ row }">
        <div
          v-if="row.phone"
          class="flex items-center text-gray-600 dark:text-gray-400"
        >
          <IconifyIcon icon="lucide:phone" class="mr-1.5 text-gray-400" />
          {{ row.phone }}
        </div>
        <span v-else class="text-gray-300">-</span>
      </template>

      <!-- 角色列 -->
      <template #role_cell="{ row }">
        <Tag
          v-if="row.roleName"
          color="processing"
          class="!m-0 flex items-center gap-1"
        >
          <IconifyIcon icon="lucide:shield" class="text-xs" />
          {{ row.roleName }}
        </Tag>
        <Tag v-else color="default" class="!m-0">
          {{ $t('admin.common.notAssigned') }}
        </Tag>
      </template>

      <!-- 类型列 -->
      <template #type_cell="{ row }">
        <Tooltip
          v-if="row.isSuper"
          :title="$t('admin.system.admin.help.superAdminHelp')"
        >
          <Badge status="error" />
          <span class="ml-1 font-medium text-destructive">
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
            <IconifyIcon
              icon="lucide:calendar"
              class="mr-1 inline-block text-gray-400"
            />
            {{ formatDateOnly(row.createdAt) }}
          </span>
          <span class="ml-4 text-gray-400">
            {{ formatTimeOnly(row.createdAt) }}
          </span>
        </div>
        <span v-else class="text-gray-300">-</span>
      </template>
    </Grid>
  </Page>
</template>
