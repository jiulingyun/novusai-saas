/**
 * 租户角色管理 - 表格列和表单配置
 * 遵循 vben-admin 规范
 */
import type { VbenFormSchema } from '#/adapter/form';
import type { OnActionClickFn, VxeTableGridOptions } from '#/adapter/vxe-table';
import type { tenantApi } from '#/api';
import { $t } from '#/locales';

type RoleInfo = tenantApi.TenantRoleInfo;

/**
 * 表格列定义
 * @param onActionClick 操作按钮点击回调
 */
export function useColumns<T = RoleInfo>(
  onActionClick: OnActionClickFn<T>,
): VxeTableGridOptions['columns'] {
  return [
    {
      field: 'roleInfo',
      title: $t('tenant.system.role.name'),
      minWidth: 260,
      treeNode: true,
      showOverflow: 'tooltip',
      slots: { default: 'role_info' },
    },
    {
      field: 'description',
      title: $t('tenant.system.role.description'),
      minWidth: 160,
      showOverflow: 'tooltip',
      slots: { default: 'desc_cell' },
    },
    {
      field: 'permissions',
      title: $t('tenant.system.role.permissions'),
      minWidth: 140,
      slots: { default: 'permissions_cell' },
    },
    {
      cellRender: {
        name: 'CellTag',
        options: [
          { color: 'success', label: $t('tenant.common.enabled'), value: true },
          { color: 'error', label: $t('tenant.common.disabled'), value: false },
        ],
      },
      field: 'isActive',
      title: $t('tenant.system.role.status'),
      width: 100,
      align: 'center',
    },
    {
      field: 'sortOrder',
      title: $t('tenant.system.role.sortOrder'),
      width: 80,
      align: 'center',
      slots: { default: 'sort_cell' },
    },
    {
      field: 'createdAt',
      title: $t('tenant.system.role.createdAt'),
      width: 160,
      slots: { default: 'time_cell' },
    },
    {
      align: 'center',
      cellRender: {
        attrs: {
          resource: 'role',  // 自动检查 role:create, role:update, role:delete
          nameField: 'name',
          nameTitle: $t('tenant.system.role.name'),
          onClick: onActionClick,
        },
        name: 'CellOperation',
        options: [
          {
            code: 'addChild',
            text: $t('tenant.system.role.addChild'),
            icon: 'lucide:plus',
            accessCodes: ['role:create'],  // addChild 映射到 create 权限
          },
          'edit',  // 自动鉴权: role:update
          'delete',  // 自动鉴权: role:delete
        ],
      },
      field: 'operation',
      fixed: 'right',
      title: $t('shared.common.operation'),
      width: 120,
    },
  ];
}

/**
 * 新建/编辑表单 Schema
 * @param isEdit 是否编辑模式
 */
export function useFormSchema(isEdit: boolean = false): VbenFormSchema[] {
  const schemas: VbenFormSchema[] = [];
  if (isEdit) {
    schemas.push({
      component: 'Input',
      componentProps: {
        disabled: true,
        placeholder: $t('tenant.system.role.placeholder.inputCode'),
      },
      fieldName: 'code',
      label: $t('tenant.system.role.code'),
    });
  }
  schemas.push(
    {
      component: 'Input',
      componentProps: {
        placeholder: $t('tenant.system.role.placeholder.inputName'),
      },
      fieldName: 'name',
      label: $t('tenant.system.role.name'),
      rules: 'required',
    },
    {
      // 父角色选择器使用插槽渲染
      component: 'Input',
      fieldName: 'parent_id',
      label: $t('tenant.system.role.parentRole'),
    },
    {
      component: 'Textarea',
      componentProps: {
        placeholder: $t('tenant.system.role.placeholder.inputDescription'),
        rows: 3,
      },
      fieldName: 'description',
      label: $t('tenant.system.role.description'),
    },
    {
      component: 'RadioGroup',
      componentProps: {
        buttonStyle: 'solid',
        options: [
          { label: $t('shared.common.enabled'), value: true },
          { label: $t('shared.common.disabled'), value: false },
        ],
        optionType: 'button',
      },
      defaultValue: true,
      fieldName: 'is_active',
      label: $t('tenant.system.role.status'),
    },
    {
      component: 'InputNumber',
      componentProps: {
        min: 0,
        placeholder: $t('tenant.system.role.placeholder.inputSortOrder'),
      },
      defaultValue: 0,
      fieldName: 'sort_order',
      label: $t('tenant.system.role.sortOrder'),
    },
    {
      // 权限树使用插槽渲染
      component: 'Input',
      fieldName: 'permission_ids',
      formItemClass: 'items-start',
      label: $t('tenant.system.role.permissions'),
    },
  );
  return schemas;
}
