<template>
  <div class="config-page">
    <div class="sidebar">
      <div
        v-for="g in groups"
        :key="g.code"
        :class="['group-item', { active: g.code === activeGroup }]"
        @click="onSelectGroup(g.code)"
      >
        <span>{{ t(g.name_key) }}</span>
      </div>
    </div>
    <div class="content">
      <div class="toolbar">
        <Button
          type="primary"
          v-access="['tenant_config:update']"
          :loading="saving"
          @click="onSave"
        >
          {{ t('shared.common.save') }}
        </Button>
      </div>
      <div v-if="loading" class="loading">{{ t('shared.common.loading') }}</div>
      <ConfigForm v-else ref="formRef" :configs="configs" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { Button, Modal } from 'ant-design-vue';
import { $t as t } from '#/locales';
import { ConfigForm } from '#/components';
import type { ConfigGroupListItemMeta, ConfigItemMeta } from '#/types/config';
import {
  getTenantConfigGroupsApi,
  getTenantConfigGroupDetailApi,
  updateTenantConfigGroupApi,
} from '#/api/tenant/configs';

const groups = ref<ConfigGroupListItemMeta[]>([]);
const activeGroup = ref<string>('');
const configs = ref<ConfigItemMeta[]>([]);
const loading = ref(false);
const saving = ref(false);
const formRef = ref<any>();
const isDirty = ref(false);

async function loadGroups() {
  groups.value = await getTenantConfigGroupsApi();
  if (groups.value.length) {
    activeGroup.value = groups.value[0]!.code;
    await loadGroupDetail(activeGroup.value);
  }
}

async function loadGroupDetail(code: string) {
  loading.value = true;
  try {
    const detail = await getTenantConfigGroupDetailApi(code);
    configs.value = (detail.configs || []).sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
    isDirty.value = false;
  } finally {
    loading.value = false;
  }
}

async function onSelectGroup(code: string) {
  if (code === activeGroup.value) return;
  if (isDirty.value) {
    Modal.confirm({
      title: t('shared.config.page.unsaved_title'),
      content: t('shared.config.page.unsaved_content'),
      okText: t('shared.common.confirm'),
      cancelText: t('shared.common.cancel'),
      onOk: async () => {
        isDirty.value = false;
        activeGroup.value = code;
        await loadGroupDetail(code);
      },
    });
  } else {
    activeGroup.value = code;
    await loadGroupDetail(code);
  }
}

async function onSave() {
  if (!activeGroup.value) return;
  await formRef.value?.validate();
  const payload = formRef.value?.prepareSubmitData();
  saving.value = true;
  try {
    await updateTenantConfigGroupApi(activeGroup.value, payload, { showSuccessMessage: true });
    isDirty.value = false;
    await loadGroupDetail(activeGroup.value);
  } finally {
    saving.value = false;
  }
}

watch(
  () => formRef.value?.getValues?.(),
  () => { isDirty.value = true; },
  { deep: true },
);

function beforeUnloadHandler(e: BeforeUnloadEvent) {
  if (isDirty.value) {
    e.preventDefault();
    e.returnValue = '';
  }
}
onMounted(() => {
  loadGroups();
  window.addEventListener('beforeunload', beforeUnloadHandler);
});
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeUnloadHandler);
});
</script>

<style scoped>
.config-page {
  display: flex;
  gap: 16px;
}
.sidebar {
  width: 240px;
  border-right: 1px solid var(--ant-color-border);
  padding-right: 12px;
}
.group-item {
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
}
.group-item.active,
.group-item:hover {
  background: var(--ant-color-fill-secondary);
}
.content {
  flex: 1;
  min-width: 0;
}
.toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
.loading {
  padding: 16px;
}
</style>
