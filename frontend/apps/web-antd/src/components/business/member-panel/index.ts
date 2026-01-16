/**
 * 成员管理面板组件
 * @description 用于展示和管理组织节点的成员列表
 */

// 组件导出
export { default as MemberPanel } from './member-panel.vue';

// 仅导出外部需要的类型
export type {
  MemberPanelProps,
  UseMemberPanelOptions,
  UseMemberPanelReturn,
} from './types';

// Composable 导出
export { useMemberPanel } from './use-member-panel';
