<script lang="ts" setup>
/**
 * 租户列表页面
 */
import type { OnActionClickParams, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { adminApi } from '#/api';

import { computed, onMounted, ref } from 'vue';

import { Page, useVbenDrawer } from '@vben/common-ui';
import { IconifyIcon, Plus } from '@vben/icons';

import { Card, Col, message, Row, Statistic } from 'ant-design-vue';

import {
  useGridSearchFormOptions,
  useVbenVxeGrid,
} from '#/adapter/vxe-table';
import { adminApi as admin } from '#/api';
import { useCrudActions } from '#/composables';
import { $t } from '#/locales';

import { PLAN_OPTIONS, useColumns, useGridFormSchema } from './data';
import Form from './modules/form.vue';

type TenantInfo = adminApi.TenantInfo;

// 新建/编辑抽屉
const [FormDrawer, formDrawerApi] = useVbenDrawer({
  connectedComponent: Form,
  destroyOnClose: true,
});

// CRUD 操作引用（用于函数提前引用）
let crud: ReturnType<typeof useCrudActions<TenantInfo>>;

/** 操作按钮点击 */
function onActionClick(e: OnActionClickParams<TenantInfo>) {
  switch (e.code) {
    case 'delete': { crud.onDelete(e.row); break; }
    case 'edit': { crud.onEdit(e.row); break; }
    case 'impersonate': { onImpersonate(e.row); break; }
  }
}

/** 状态切换 */
function handleToggleStatus(newStatus: boolean, row: TenantInfo) {
  return crud.onToggleStatus(newStatus, row);
}

// 表格
const [Grid, gridApi] = useVbenVxeGrid({
  formOptions: useGridSearchFormOptions(useGridFormSchema()),
  gridOptions: {
    columns: useColumns<TenantInfo>(onActionClick, handleToggleStatus),
    keepSource: true,
    pagerConfig: { enabled: true },
    proxyConfig: {
      ajax: {
        query: async ({ page }, formValues) => {
          return await admin.getTenantListApi({
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
    toolbarConfig: { custom: true, refresh: true, search: true, zoom: true },
  } as VxeTableGridOptions<TenantInfo>,
});

// CRUD 操作
crud = useCrudActions<TenantInfo>({
  gridApi,
  formDrawerApi,
  deleteApi: admin.deleteTenantApi,
  toggleStatusApi: admin.toggleTenantStatusApi,
  i18nPrefix: 'admin.tenant',
});

const { onCreate, onRefresh } = crud;

/**
 * 一键登录租户后台
 */
async function onImpersonate(row: TenantInfo) {
  const hideLoading = message.loading({
    content: $t('admin.tenant.messages.impersonating', { name: row.name }),
    duration: 0,
    key: 'impersonate_tenant',
  });
  try {
    const result = await admin.tenantImpersonateApi(row.id);
    message.success({
      content: $t('admin.tenant.messages.impersonateSuccess'),
      key: 'impersonate_tenant',
    });
    // 构建跳转 URL 并在新窗口打开
    const targetUrl = `/tenant/impersonate?token=${encodeURIComponent(result.impersonateToken)}`;
    window.open(targetUrl, '_blank');
  } catch {
    hideLoading();
    message.error({
      content: $t('admin.tenant.messages.impersonateFailed'),
      key: 'impersonate_tenant',
    });
  }
}

// ============ 统计数据 ============
interface TenantStats {
  total: number;
  active: number;
  inactive: number;
  expired: number;
  byPlan: Record<string, number>;
}

const stats = ref<TenantStats>({
  total: 0,
  active: 0,
  inactive: 0,
  expired: 0,
  byPlan: {},
});
const loadingStats = ref(false);

// 计算各套餐统计
const planStats = computed(() => {
  return PLAN_OPTIONS.map((option) => ({
    ...option,
    count: stats.value.byPlan[option.value] || 0,
  }));
});

async function loadStats() {
  loadingStats.value = true;
  try {
    // 获取数据计算统计
    const res = await admin.getTenantListApi({
      'page[number]': 1,
      'page[size]': 100,
    });
    const items = res.items || [];
    const now = new Date();

    const byPlan: Record<string, number> = {};
    let active = 0;
    let inactive = 0;
    let expired = 0;

    items.forEach((item: TenantInfo) => {
      // 套餐统计
      byPlan[item.plan] = (byPlan[item.plan] || 0) + 1;

      // 状态统计
      if (item.isActive) {
        active++;
      } else {
        inactive++;
      }

      // 过期统计
      if (item.expiresAt && new Date(item.expiresAt) < now) {
        expired++;
      }
    });

    stats.value = {
      total: items.length,
      active,
      inactive,
      expired,
      byPlan,
    };
  } finally {
    loadingStats.value = false;
  }
}

onMounted(() => {
  loadStats();
});
</script>

<template>
  <Page auto-content-height content-class="flex flex-col gap-4">
    <FormDrawer @success="onRefresh" />

    <!-- 统计卡片 -->
    <Row :gutter="16">
      <Col :span="6">
        <Card class="stat-card" :loading="loadingStats">
          <Statistic
            :title="$t('admin.tenant.stats.total')"
            :value="stats.total"
            :value-style="{ color: '#1890ff', fontWeight: 600 }"
          >
            <template #prefix>
              <IconifyIcon icon="lucide:building-2" class="mr-2" />
            </template>
          </Statistic>
        </Card>
      </Col>
      <Col :span="6">
        <Card class="stat-card" :loading="loadingStats">
          <Statistic
            :title="$t('admin.tenant.stats.active')"
            :value="stats.active"
            :value-style="{ color: '#52c41a', fontWeight: 600 }"
          >
            <template #prefix>
              <IconifyIcon icon="lucide:check-circle" class="mr-2" />
            </template>
          </Statistic>
        </Card>
      </Col>
      <Col :span="6">
        <Card class="stat-card" :loading="loadingStats">
          <Statistic
            :title="$t('admin.tenant.stats.expired')"
            :value="stats.expired"
            :value-style="{
              color: stats.expired > 0 ? '#ff4d4f' : '#8c8c8c',
              fontWeight: 600,
            }"
          >
            <template #prefix>
              <IconifyIcon icon="lucide:clock" class="mr-2" />
            </template>
          </Statistic>
        </Card>
      </Col>
      <Col :span="6">
        <Card class="stat-card" :loading="loadingStats">
          <Statistic
            :title="$t('admin.tenant.stats.inactive')"
            :value="stats.inactive"
            :value-style="{
              color: stats.inactive > 0 ? '#faad14' : '#8c8c8c',
              fontWeight: 600,
            }"
          >
            <template #prefix>
              <IconifyIcon icon="lucide:ban" class="mr-2" />
            </template>
          </Statistic>
        </Card>
      </Col>
    </Row>

    <!-- 套餐分布 -->
    <Row :gutter="16">
      <Col v-for="plan in planStats" :key="plan.value" :span="6">
        <Card class="stat-card stat-card-small" :loading="loadingStats">
          <div class="flex items-center justify-between">
            <span class="text-gray-500">{{ plan.label }}</span>
            <span class="text-lg font-semibold">{{ plan.count }}</span>
          </div>
        </Card>
      </Col>
    </Row>

    <!-- 表格 -->
    <Card class="flex-1" :body-style="{ padding: '16px', height: '100%' }">
      <Grid>
        <template #toolbar-tools>
          <Card size="small" class="mr-4 !border-primary/20 !bg-primary/5">
            <span class="text-sm text-gray-600">{{
              $t('admin.tenant.tip')
            }}</span>
          </Card>
        <Card
            v-access:code="['tenant:create']"
            size="small"
            class="mr-2 cursor-pointer transition-shadow duration-200 hover:shadow-md"
            @click="onCreate"
          >
            <div class="flex items-center gap-2 text-primary">
              <Plus class="size-4" />
              <span class="font-medium">{{ $t('admin.tenant.create') }}</span>
            </div>
          </Card>
        </template>
      </Grid>
    </Card>
  </Page>
</template>

<style scoped>
.stat-card {
  border-radius: 8px;
  transition: box-shadow 0.2s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgb(0 0 0 / 10%);
}

.stat-card-small {
  padding: 8px 16px;
}

.stat-card-small :deep(.ant-card-body) {
  padding: 12px 16px;
}
</style>
