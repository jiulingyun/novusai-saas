<script lang="ts" setup>
/**
 * 租户角色列表页面
 * 使用 Tailwind CSS 自定义树形结构
 */
import type { tenantApi } from '#/api';

import { computed, onMounted, ref } from 'vue';

import { Page, useVbenDrawer, VbenLoading } from '@vben/common-ui';
import { IconifyIcon, Plus } from '@vben/icons';

import { Button, Empty, message, Tooltip } from 'ant-design-vue';

import { tenantApi as tenant } from '#/api';
import { RoleTreeNode } from '#/components/business/role-tree';
import type { RoleTreeNodeData } from '#/components/business/role-tree';
import { $t } from '#/locales';
import {
  buildTree,
  confirmDelete,
  getLevelColor,
  useTreeExpand,
} from '#/utils/common';

import Form from './modules/form.vue';

type RoleInfo = tenantApi.TenantRoleInfo;

// 新建/编辑抽屉
const [FormDrawer, formDrawerApi] = useVbenDrawer({
  connectedComponent: Form,
  destroyOnClose: true,
});

// 数据状态
const loading = ref(false);
const roles = ref<RoleInfo[]>([]);

// 展开状态管理
const { expandedIds, toggle, expandAll, collapseAll, isExpanded } =
  useTreeExpand(() => roles.value, false);

// 将平铺数据构建为树形结构
const treeData = computed(() =>
  buildTree<RoleInfo>(roles.value) as RoleTreeNodeData[]
);

/**
 * 加载数据
 */
async function loadData() {
  loading.value = true;
  try {
    roles.value = await tenant.getTenantRoleListApi();
    // 默认展开所有
    expandAll();
  } catch {
    roles.value = [];
  } finally {
    loading.value = false;
  }
}

/**
 * 编辑
 */
function onEdit(row: RoleTreeNodeData) {
  formDrawerApi.setData({ ...row, mode: 'edit' }).open();
}

/**
 * 添加子角色
 */
function onAddChild(row: RoleTreeNodeData) {
  formDrawerApi.setData({ mode: 'add', parentId: row.id }).open();
}

/**
 * 删除
 */
function onDelete(row: RoleTreeNodeData) {
  confirmDelete({
    row,
    nameField: 'name',
    deleteApi: (id) => tenant.deleteTenantRoleApi(id),
    onSuccess: loadData,
    i18nPrefix: 'tenant.system.role',
  });
}

/**
 * 新建
 */
function onCreate() {
  formDrawerApi.setData({ mode: 'add' }).open();
}

/**
 * 刷新
 */
function onRefresh() {
  loadData();
}

/**
 * 切换状态
 */
async function onToggleStatus(row: RoleTreeNodeData, isActive: boolean) {
  try {
    await tenant.updateTenantRoleApi(row.id, { is_active: isActive });
    message.success(isActive ? $t('shared.common.statusEnabled') : $t('shared.common.statusDisabled'));
    // 直接更新本地数据，避免重新加载
    const target = roles.value.find((r) => r.id === row.id);
    if (target) target.isActive = isActive;
  } catch {
    // 失败时不做处理，Switch 会保持原状态
  }
}

onMounted(loadData);
</script>

<template>
  <Page auto-content-height>
    <FormDrawer @success="onRefresh" />

    <div class="flex h-full flex-col overflow-hidden rounded-xl bg-card shadow-sm">
      <!-- 工具栏 -->
      <div class="flex items-center justify-between border-b border-border/50 bg-card/80 px-6 py-4 backdrop-blur-sm">
        <div class="flex items-center gap-3">
          <div class="flex size-10 items-center justify-center rounded-xl bg-primary/10">
            <IconifyIcon icon="lucide:shield" class="size-5 text-primary" />
          </div>
          <div>
            <h2 class="text-lg font-semibold">{{ $t('tenant.system.role.title') }}</h2>
            <p class="text-xs text-muted-foreground">{{ $t('shared.common.totalCount', { count: roles.length }) }}</p>
          </div>
        </div>
        <div class="flex items-center gap-1">
          <Tooltip :title="$t('shared.common.expandAll')">
            <Button type="text" class="!size-9 !rounded-lg" @click="expandAll">
              <IconifyIcon icon="lucide:unfold-vertical" class="size-4" />
            </Button>
          </Tooltip>
          <Tooltip :title="$t('shared.common.collapseAll')">
            <Button type="text" class="!size-9 !rounded-lg" @click="collapseAll">
              <IconifyIcon icon="lucide:fold-vertical" class="size-4" />
            </Button>
          </Tooltip>
          <Tooltip :title="$t('shared.common.refresh')">
            <Button type="text" class="!size-9 !rounded-lg" @click="onRefresh">
              <IconifyIcon icon="lucide:refresh-cw" class="size-4" />
            </Button>
          </Tooltip>
          <div class="mx-2 h-5 w-px bg-border" />
          <Button
            v-access:code="['role:create']"
            type="primary"
            class="!rounded-lg !px-4"
            @click="onCreate"
          >
            <Plus class="mr-1.5 size-4" />
            {{ $t('tenant.system.role.create') }}
          </Button>
        </div>
      </div>

      <!-- 树形列表 -->
      <div class="flex-1 overflow-auto p-4">
        <VbenLoading v-if="loading" spinning class="h-40" />
        <Empty v-else-if="treeData.length === 0" :description="$t('shared.common.noData')" />
        <div v-else class="space-y-0.5">
          <RoleTreeNode
            v-for="node in treeData"
            :key="node.id"
            :node="node"
            :level="0"
            :expanded-ids="expandedIds"
            :get-level-color="getLevelColor"
            :is-expanded="isExpanded"
            i18n-prefix="tenant"
            @toggle="toggle"
            @edit="onEdit"
            @add-child="onAddChild"
            @delete="onDelete"
            @toggle-status="onToggleStatus"
          />
        </div>
      </div>
    </div>
  </Page>
</template>
