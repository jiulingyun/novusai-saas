/**
 * 控制台消息过滤器
 * 过滤掉框架产生的特定错误消息，避免干扰开发体验
 */

// 保存原始的 console.error 方法
const originalConsoleError = console.error;

/**
 * 需要过滤的错误消息模式
 * 这些错误会被转换为更友好的提示，或直接忽略
 */
const FILTERED_ERROR_PATTERNS = [
  // 框架的路由组件无效错误 - 已在 menu-transformer 中输出友好提示
  /route component is invalid:/i,
];

/**
 * 设置控制台过滤器
 * 过滤掉框架产生的组件错误消息，因为我们已经在 menu-transformer 中输出了更友好的提示
 */
export function setupConsoleFilter(): void {
  console.error = (...args: any[]) => {
    // 检查第一个参数是否匹配需要过滤的模式
    const firstArg = args[0];
    if (typeof firstArg === 'string') {
      for (const pattern of FILTERED_ERROR_PATTERNS) {
        if (pattern.test(firstArg)) {
          // 跳过这条错误消息，因为已在 menu-transformer 中输出友好提示
          return;
        }
      }
    }

    // 其他错误正常输出
    originalConsoleError.apply(console, args);
  };
}

/**
 * 恢复原始的 console.error
 * 用于测试或需要查看完整错误信息的场景
 */
export function restoreConsoleError(): void {
  console.error = originalConsoleError;
}
