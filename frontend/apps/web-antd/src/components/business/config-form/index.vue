<template>
  <Form
    layout="vertical"
    :model="formModel"
    :rules="formRules"
    ref="formRef"
    :disabled="disabled"
  >
    <Form.Item
      v-for="cfg in orderedConfigs"
      :key="cfg.key"
      :name="cfg.key"
      :label="t(cfg.name_key)"
      :extra="cfg.description_key ? t(cfg.description_key) : undefined"
    >
      <!-- string -->
      <Input v-if="cfg.value_type === 'string'" v-model:value="formModel[cfg.key]" />

      <!-- number -->
      <InputNumber
        v-else-if="cfg.value_type === 'number'"
        v-model:value="formModel[cfg.key]"
        :style="{ width: '100%' }"
        :min="getRuleNumber(cfg, 'min_value')"
        :max="getRuleNumber(cfg, 'max_value')"
      />

      <!-- boolean -->
      <Switch v-else-if="cfg.value_type === 'boolean'" v-model:checked="formModel[cfg.key]" />

      <!-- select -->
      <Select
        v-else-if="cfg.value_type === 'select'"
        v-model:value="formModel[cfg.key]"
        :options="(cfg.options || []).map((o) => ({ value: o.value, label: t(o.label_key) }))"
      />

      <!-- multi_select -->
      <Select
        v-else-if="cfg.value_type === 'multi_select'"
        v-model:value="formModel[cfg.key]"
        mode="multiple"
        :options="(cfg.options || []).map((o) => ({ value: o.value, label: t(o.label_key) }))"
      />

      <!-- text -->
      <Input.TextArea v-else-if="cfg.value_type === 'text'" v-model:value="formModel[cfg.key]" :rows="4" />

      <!-- password -->
      <Input.Password
        v-else-if="cfg.value_type === 'password'"
        v-model:value="formModel[cfg.key]"
        :autocomplete="'new-password'"
        :placeholder="t('shared.config.page.password_placeholder')"
      />

      <!-- color (fallback to input type=color + text) -->
      <div v-else-if="cfg.value_type === 'color'" style="display: flex; gap: 8px; align-items: center">
        <input type="color" :value="formModel[cfg.key]" @input="(e) => formModel[cfg.key] = (e.target as HTMLInputElement).value" />
        <Input v-model:value="formModel[cfg.key]" style="width: 120px" />
      </div>

      <!-- image -->
      <ImageUpload v-else-if="cfg.value_type === 'image'" v-model="formModel[cfg.key]" />

      <!-- json (fallback: textarea) -->
      <Input.TextArea v-else v-model:value="formModel[cfg.key]" :rows="6" />
    </Form.Item>
  </Form>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { $t as t } from '#/locales';
import type { Rule } from 'ant-design-vue/es/form';
import { Form, Input, InputNumber, Select, Switch } from 'ant-design-vue';
import type { FormInstance } from 'ant-design-vue';

import ImageUpload from '../image-upload/image-upload.vue';
import type {
  ConfigItemMeta,
  ValidationRuleMeta,
  ConfigSubmitPayload,
} from '#/types/config';

interface Props {
  configs: ConfigItemMeta[];
  disabled?: boolean;
}

const props = defineProps<Props>();
const formRef = ref<FormInstance>();
const formModel = reactive<Record<string, any>>({});

// 初始化表单值
watch(
  () => props.configs,
  (list) => {
    const data: Record<string, any> = {};
    (list || []).forEach((cfg) => {
      const raw = cfg.value ?? cfg.default_value;
      data[cfg.key] = cfg.value_type === 'password' && cfg.is_encrypted ? '******' : raw;
    });
    Object.assign(formModel, data);
  },
  { immediate: true },
);

const orderedConfigs = computed(() => {
  return [...(props.configs || [])].sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
});

const formRules = computed<Record<string, Rule[]>>(() => {
  const rules: Record<string, Rule[]> = {};
  (props.configs || []).forEach((cfg) => {
    rules[cfg.key] = convertRules(cfg);
  });
  return rules;
});

function convertRules(cfg: ConfigItemMeta): Rule[] {
  const rules: Rule[] = [];
  if (cfg.is_required) {
    rules.push({ required: true, message: t('shared.config.validation.required', { field: t(cfg.name_key) }) });
  }
  (cfg.validation_rules || []).forEach((r: ValidationRuleMeta) => {
    switch (r.type) {
      case 'min_length':
        rules.push({ min: Number(r.value), message: t(r.message_key, { min: r.value }) });
        break;
      case 'max_length':
        rules.push({ max: Number(r.value), message: t(r.message_key, { max: r.value }) });
        break;
      case 'min_value':
        rules.push({ type: 'number', min: Number(r.value), message: t(r.message_key, { min: r.value }) });
        break;
      case 'max_value':
        rules.push({ type: 'number', max: Number(r.value), message: t(r.message_key, { max: r.value }) });
        break;
      case 'pattern':
        rules.push({ pattern: new RegExp(String(r.value)), message: t(r.message_key) });
        break;
    }
  });
  return rules;
}

function getRuleNumber(cfg: ConfigItemMeta, type: 'min_value' | 'max_value'): number | undefined {
  const rule = (cfg.validation_rules || []).find((r) => r.type === type);
  return rule ? Number(rule.value) : undefined;
}

async function validate() {
  await formRef.value?.validate();
}

function getValues(): Record<string, any> {
  return { ...formModel };
}

function prepareSubmitData(): ConfigSubmitPayload {
  const payload: ConfigSubmitPayload = {};
  (props.configs || []).forEach((cfg) => {
    const val = formModel[cfg.key];
    if (cfg.value_type === 'password' && cfg.is_encrypted) {
      if (val && val !== '******') {
        payload[cfg.key] = val;
      }
    } else {
      payload[cfg.key] = val;
    }
  });
  return payload;
}

function reset() {
  formRef.value?.resetFields();
}

// 暴露方法给父组件
defineExpose({ validate, getValues, prepareSubmitData, reset, formRef });
</script>

<style scoped>
</style>
