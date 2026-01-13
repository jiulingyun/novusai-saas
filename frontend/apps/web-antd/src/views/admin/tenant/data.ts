/**
 * 租户管理 - 表格列和表单配置
 * 遵循 vben-admin 规范
 */
import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { adminApi } from '#/api';

import { $t } from '#/locales';
import { ADMIN_PERMISSIONS } from '#/utils/access';

type TenantInfo = adminApi.TenantInfo;
type TenantPlan = adminApi.TenantPlan;

/**
 * 套餐选项
 */
export function getPlanOptions(): { label: string; value: TenantPlan }[] {
  return [
    { label: $t('admin.tenant.planOptions.free'), value: 'free' },
    { label: $t('admin.tenant.planOptions.basic'), value: 'basic' },
    { label: $t('admin.tenant.planOptions.pro'), value: 'pro' },
    { label: $t('admin.tenant.planOptions.enterprise'), value: 'enterprise' },
  ];
}

// For backward compatibility
export const PLAN_OPTIONS = [
  { label: '免费版', value: 'free' },
  { label: '基础版', value: 'basic' },
  { label: '专业版', value: 'pro' },
  { label: '企业版', value: 'enterprise' },
] as { label: string; value: TenantPlan }[];

/**
 * 获取套餐显示文本
 */
export function getPlanText(plan: TenantPlan): string {
  const key = `admin.tenant.planOptions.${plan}`;
  return $t(key);
}

/**
 * 获取套餐颜色
 */
export function getPlanColor(plan: TenantPlan): string {
  switch (plan) {
    case 'basic': {
      return 'blue';
    }
    case 'enterprise': {
      return 'gold';
    }
    case 'free': {
      return 'default';
    }
    case 'pro': {
      return 'green';
    }
    default: {
      return 'default';
    }
  }
}

/**
 * 表格列定义
 * @param onActionClick 操作按钮点击回调
 * @param onStatusChange 状态切换回调
 */
export function useColumns<T = TenantInfo>(
  onActionClick: OnActionClickFn<T>,
  onStatusChange?: (newStatus: boolean, row: T) => Promise<boolean | undefined>,
): VxeTableGridOptions['columns'] {
  return [
    {
      field: 'code',
      title: $t('admin.tenant.code'),
      minWidth: 120,
      className: 'font-mono text-gray-500',
    },
    {
      field: 'name',
      title: $t('admin.tenant.name'),
      minWidth: 150,
      className: 'font-medium',
    },
    {
      field: 'contactName',
      title: $t('admin.tenant.contactName'),
      width: 100,
      formatter: ({ cellValue }) => cellValue || '-',
    },
    {
      field: 'contactPhone',
      title: $t('admin.tenant.contactPhone'),
      width: 130,
      formatter: ({ cellValue }) => cellValue || '-',
    },
    {
      cellRender: {
        name: 'CellTag',
        props: ({ row }: { row: TenantInfo }) => ({
          color: getPlanColor(row.plan),
        }),
      },
      field: 'plan',
      formatter: ({ cellValue }) => getPlanText(cellValue),
      title: $t('admin.tenant.plan'),
      width: 100,
      align: 'center',
    },
    {
      cellRender: {
        attrs: {
          beforeChange: onStatusChange,
          checkedValue: true,
          unCheckedValue: false,
        },
        name: onStatusChange ? 'CellSwitch' : 'CellTag',
        options: [
          { color: 'success', label: $t('admin.common.enabled'), value: true },
          {
            color: 'error',
            label: $t('admin.common.disabled'),
            value: false,
          },
        ],
      },
      field: 'isActive',
      title: $t('admin.tenant.status'),
      width: 90,
      align: 'center',
    },
    {
      cellRender: {
        name: 'CellTag',
        props: ({ row }: { row: TenantInfo }) => {
          if (!row.expiresAt) return { color: 'success' };
          const isExpired = new Date(row.expiresAt) < new Date();
          const isNearExpiry =
            !isExpired &&
            new Date(row.expiresAt) <
              new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
          return {
            color: isExpired ? 'error' : isNearExpiry ? 'warning' : 'default',
          };
        },
      },
      field: 'expiresAt',
      formatter: ({ cellValue }) => {
        if (!cellValue) return $t('admin.tenant.expiryStatus.permanent');
        return new Date(cellValue).toLocaleDateString();
      },
      title: $t('admin.tenant.expiresAt'),
      width: 120,
      align: 'center',
    },
    {
      field: 'createdAt',
      formatter: ({ cellValue }) => {
        if (!cellValue) return '-';
        return new Date(cellValue).toLocaleString();
      },
      title: $t('admin.tenant.createdAt'),
      width: 170,
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          nameField: 'name',
          nameTitle: $t('admin.tenant.name'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'edit',
            text: $t('common.edit'),
            icon: 'lucide:edit',
            accessCodes: [ADMIN_PERMISSIONS.TENANT_UPDATE],
          },
          {
            code: 'delete',
            text: $t('common.delete'),
            icon: 'lucide:trash-2',
            accessCodes: [ADMIN_PERMISSIONS.TENANT_DELETE],
          },
        ],
      },
      field: 'operation',
      fixed: 'right',
      title: $t('admin.common.operation'),
      width: 80,
    },
  ];
}

/**
 * 搜索表单 Schema
 */
export function useGridFormSchema(): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      componentProps: {
        allowClear: true,
        placeholder: $t('admin.tenant.placeholder.searchName'),
      },
      fieldName: 'name',
      label: $t('admin.tenant.name'),
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: [
          { label: $t('admin.common.enabled'), value: true },
          { label: $t('admin.common.disabled'), value: false },
        ],
        placeholder: $t('admin.tenant.placeholder.allStatus'),
      },
      fieldName: 'is_active',
      label: $t('admin.tenant.status'),
    },
    {
      component: 'Select',
      componentProps: {
        allowClear: true,
        options: getPlanOptions(),
        placeholder: $t('admin.tenant.placeholder.allPlan'),
      },
      fieldName: 'plan',
      label: $t('admin.tenant.plan'),
    },
  ];
}

/**
 * 新建/编辑表单 Schema
 * @param isEdit 是否编辑模式
 */
export function useFormSchema(isEdit: boolean = false): VbenFormSchema[] {
  return [
    {
      component: 'Input',
      componentProps: {
        disabled: isEdit,
        placeholder: $t('admin.tenant.placeholder.inputCode'),
      },
      fieldName: 'code',
      help: $t('admin.tenant.help.codeFormat'),
      label: $t('admin.tenant.code'),
      rules: isEdit ? undefined : 'required',
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('admin.tenant.placeholder.inputName'),
      },
      fieldName: 'name',
      label: $t('admin.tenant.name'),
      rules: 'required',
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('admin.tenant.placeholder.inputContactName'),
      },
      fieldName: 'contact_name',
      label: $t('admin.tenant.contactName'),
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('admin.tenant.placeholder.inputContactPhone'),
      },
      fieldName: 'contact_phone',
      label: $t('admin.tenant.contactPhone'),
    },
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('admin.tenant.placeholder.inputContactEmail'),
        type: 'email',
      },
      fieldName: 'contact_email',
      label: $t('admin.tenant.contactEmail'),
    },
    {
      component: 'Select',
      componentProps: {
        options: getPlanOptions(),
        placeholder: $t('admin.tenant.placeholder.selectPlan'),
      },
      defaultValue: 'free',
      fieldName: 'plan',
      label: $t('admin.tenant.plan'),
    },
    {
      component: 'DatePicker',
      componentProps: {
        format: 'YYYY-MM-DD',
        placeholder: $t('admin.tenant.placeholder.selectExpiresAt'),
        valueFormat: 'YYYY-MM-DD',
      },
      fieldName: 'expires_at',
      label: $t('admin.tenant.expiresAt'),
    },
    {
      component: 'Textarea',
      componentProps: {
        placeholder: $t('admin.tenant.placeholder.inputRemark'),
        rows: 3,
      },
      fieldName: 'remark',
      label: $t('admin.tenant.remark'),
    },
  ];
}
