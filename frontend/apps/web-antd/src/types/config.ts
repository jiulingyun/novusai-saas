/**
 * 系统配置模块 - 前端类型定义
 */

export type ConfigValueType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'select'
  | 'multi_select'
  | 'json'
  | 'text'
  | 'password'
  | 'color'
  | 'image';

export interface ValidationRuleMeta {
  type: 'min_length' | 'max_length' | 'min_value' | 'max_value' | 'pattern';
  value: number | string;
  message_key: string;
}

export interface ConfigOptionMeta {
  value: string;
  label_key: string;
}

export interface ConfigItemMeta {
  key: string;
  name_key: string;
  description_key?: string;
  value_type: ConfigValueType;
  value?: any;
  default_value?: any;
  options?: ConfigOptionMeta[];
  validation_rules?: ValidationRuleMeta[];
  is_required?: boolean;
  is_encrypted?: boolean;
  sort_order?: number;
}

export interface ConfigGroupListItemMeta {
  code: string;
  name_key: string;
  description_key?: string;
  icon?: string;
  sort_order: number;
  config_count: number;
}

export interface ConfigGroupMeta {
  code: string;
  name_key: string;
  description_key?: string;
  icon?: string;
  sort_order: number;
  configs: ConfigItemMeta[];
}

export type ConfigSubmitPayload = Record<string, any>;
