/**
 * HTTP 请求客户端
 *
 * 基于 axios 封装，支持：
 * - 多端 Token 自动携带
 * - 重复请求取消
 * - Loading 状态管理
 * - 业务错误码处理
 * - Token 自动刷新
 * - 文件上传下载
 * - SSE 流式请求
 *
 * @module utils/request/request-client
 */
import type { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

import type {
  ApiEndpoint,
  HttpResponse,
  ParamsSerializer,
  RequestClientConfig,
  RequestClientOptions,
  RequestInterceptorConfig,
  RequestOptions,
  ResponseInterceptorConfig,
  SseRequestOptions,
  UploadFileData,
  UploadProgressCallback,
} from './types';

import axios from 'axios';
import qs from 'qs';

// ============================================================
// 默认配置
// ============================================================

/** 默认请求选项 */
const DEFAULT_OPTIONS: Required<RequestOptions> = {
  cancelDuplicateRequest: true,
  loading: false,
  responseReturn: 'data',
  showErrorMessage: true,
  showCodeMessage: true,
  showSuccessMessage: false,
  successMessage: '',
  paramsSerializer: 'brackets',
};

// ============================================================
// 工具函数
// ============================================================

/**
 * 获取参数序列化器
 */
function getParamsSerializer(type: ParamsSerializer) {
  const formatMap: Record<ParamsSerializer, 'brackets' | 'comma' | 'indices' | 'repeat'> = {
    brackets: 'brackets',
    comma: 'comma',
    indices: 'indices',
    repeat: 'repeat',
  };
  return (params: any) => qs.stringify(params, { arrayFormat: formatMap[type] });
}

/**
 * 根据请求 URL 判断端类型
 */
function getEndpointByUrl(url: string): ApiEndpoint {
  if (url.startsWith('/admin')) return 'admin';
  if (url.startsWith('/tenant')) return 'tenant';
  return 'user';
}

/**
 * 生成请求唯一标识（用于重复请求判断）
 */
function getPendingKey(config: InternalAxiosRequestConfig): string {
  const { url, method, params, data, headers } = config;
  const dataStr = typeof data === 'string' ? data : JSON.stringify(data);
  return [
    url,
    method,
    JSON.stringify(params),
    dataStr,
    (headers as any)?.Authorization || '',
  ].join('&');
}

// ============================================================
// RequestClient 类
// ============================================================

export class RequestClient {
  /** Axios 实例 */
  public readonly instance: AxiosInstance;

  /** 默认选项 */
  private readonly defaultOptions: Required<RequestOptions>;

  /** 正在刷新 Token */
  public isRefreshing = false;

  /** Token 刷新队列 */
  public refreshTokenQueue: Array<(token: string) => void> = [];

  /** 待处理请求 Map（用于取消重复请求） */
  private pendingMap = new Map<string, AbortController>();

  /** Loading 计数 */
  private loadingCount = 0;

  /** Token 获取函数 */
  private getToken?: (endpoint: ApiEndpoint) => string | null;

  /** Refresh Token 获取函数（拦截器使用） */
  public getRefreshToken?: (endpoint: ApiEndpoint) => string | null;

  /** Token 刷新函数（拦截器使用） */
  public doRefreshToken?: () => Promise<string>;

  /** 重新认证函数（拦截器使用） */
  public doReAuthenticate?: () => Promise<void>;

  /** 显示 Loading */
  private showLoading?: () => void;

  /** 隐藏 Loading */
  private hideLoading?: () => void;

  /** 显示消息（拦截器使用） */
  public showMessage?: (type: 'error' | 'success', message: string) => void;

  /** 国际化函数（拦截器使用） */
  public t?: (key: string) => string;

  constructor(options: RequestClientOptions = {}) {
    const {
      baseURL,
      timeout = 10_000,
      headers = {},
      ...restOptions
    } = options;

    // 合并默认选项
    this.defaultOptions = { ...DEFAULT_OPTIONS, ...restOptions };

    // 创建 Axios 实例
    this.instance = axios.create({
      baseURL,
      timeout,
      headers: {
        'Content-Type': 'application/json;charset=utf-8',
        ...headers,
      },
      paramsSerializer: getParamsSerializer(this.defaultOptions.paramsSerializer),
    });

    // 绑定方法
    this.bindMethods();
  }

  /** 绑定方法上下文 */
  private bindMethods() {
    this.get = this.get.bind(this);
    this.post = this.post.bind(this);
    this.put = this.put.bind(this);
    this.delete = this.delete.bind(this);
    this.request = this.request.bind(this);
    this.upload = this.upload.bind(this);
    this.download = this.download.bind(this);
    this.requestSSE = this.requestSSE.bind(this);
    this.postSSE = this.postSSE.bind(this);
  }

  // ============================================================
  // 配置方法
  // ============================================================

  /** 设置 Token 获取函数 */
  setTokenGetter(fn: (endpoint: ApiEndpoint) => string | null) {
    this.getToken = fn;
    return this;
  }

  /** 设置 Refresh Token 获取函数 */
  setRefreshTokenGetter(fn: (endpoint: ApiEndpoint) => string | null) {
    this.getRefreshToken = fn;
    return this;
  }

  /** 设置 Token 刷新函数 */
  setRefreshTokenHandler(fn: () => Promise<string>) {
    this.doRefreshToken = fn;
    return this;
  }

  /** 设置重新认证函数 */
  setReAuthenticateHandler(fn: () => Promise<void>) {
    this.doReAuthenticate = fn;
    return this;
  }

  /** 设置 Loading 处理函数 */
  setLoadingHandler(show: () => void, hide: () => void) {
    this.showLoading = show;
    this.hideLoading = hide;
    return this;
  }

  /** 设置消息提示函数 */
  setMessageHandler(fn: (type: 'error' | 'success', message: string) => void) {
    this.showMessage = fn;
    return this;
  }

  /** 设置国际化函数 */
  setI18n(fn: (key: string) => string) {
    this.t = fn;
    return this;
  }

  // ============================================================
  // 拦截器方法
  // ============================================================

  /** 添加请求拦截器 */
  addRequestInterceptor(config: RequestInterceptorConfig) {
    this.instance.interceptors.request.use(
      config.fulfilled as any,
      config.rejected,
    );
    return this;
  }

  /** 添加响应拦截器 */
  addResponseInterceptor(config: ResponseInterceptorConfig) {
    this.instance.interceptors.response.use(
      config.fulfilled as any,
      config.rejected,
    );
    return this;
  }

  // ============================================================
  // 重复请求取消
  // ============================================================

  /** 添加待处理请求（拦截器使用） */
  public addPending(config: InternalAxiosRequestConfig) {
    const key = getPendingKey(config);
    if (this.pendingMap.has(key)) {
      // 取消之前的请求
      const controller = this.pendingMap.get(key)!;
      controller.abort();
      this.pendingMap.delete(key);
    }
    const controller = new AbortController();
    config.signal = controller.signal;
    this.pendingMap.set(key, controller);
  }

  /** 移除待处理请求（拦截器使用） */
  public removePending(config: InternalAxiosRequestConfig) {
    const key = getPendingKey(config);
    this.pendingMap.delete(key);
  }

  // ============================================================
  // Loading 管理
  // ============================================================

  /** 开启 Loading */
  private openLoading() {
    this.loadingCount++;
    if (this.loadingCount === 1 && this.showLoading) {
      this.showLoading();
    }
  }

  /** 关闭 Loading */
  private closeLoading() {
    if (this.loadingCount > 0) {
      this.loadingCount--;
    }
    if (this.loadingCount === 0 && this.hideLoading) {
      this.hideLoading();
    }
  }

  // ============================================================
  // HTTP 方法
  // ============================================================

  /** GET 请求 */
  get<T = any>(url: string, config?: RequestClientConfig): Promise<T> {
    return this.request<T>(url, { ...config, method: 'GET' });
  }

  /** POST 请求 */
  post<T = any>(url: string, data?: any, config?: RequestClientConfig): Promise<T> {
    return this.request<T>(url, { ...config, data, method: 'POST' });
  }

  /** PUT 请求 */
  put<T = any>(url: string, data?: any, config?: RequestClientConfig): Promise<T> {
    return this.request<T>(url, { ...config, data, method: 'PUT' });
  }

  /** DELETE 请求 */
  delete<T = any>(url: string, config?: RequestClientConfig): Promise<T> {
    return this.request<T>(url, { ...config, method: 'DELETE' });
  }

  /** PATCH 请求 */
  patch<T = any>(url: string, data?: any, config?: RequestClientConfig): Promise<T> {
    return this.request<T>(url, { ...config, data, method: 'PATCH' });
  }

  /**
   * 通用请求方法
   */
  async request<T = any>(url: string, config: RequestClientConfig = {}): Promise<T> {
    // 合并选项
    const options: Required<RequestOptions> = {
      ...this.defaultOptions,
      ...config,
    };

    // 开启 Loading
    if (options.loading) {
      this.openLoading();
    }

    try {
      const response = await this.instance.request<T, AxiosResponse<HttpResponse<T>>>({
        url,
        ...config,
        // 存储选项到 config 中，供拦截器使用
        ...({ __options: options } as any),
      });

      return response as unknown as T;
    } catch (error: any) {
      throw error;
    } finally {
      // 关闭 Loading
      if (options.loading) {
        this.closeLoading();
      }
    }
  }

  // ============================================================
  // 文件上传
  // ============================================================

  /**
   * 文件上传
   */
  async upload<T = any>(
    url: string,
    data: UploadFileData,
    config?: RequestClientConfig,
    onProgress?: UploadProgressCallback,
  ): Promise<T> {
    const formData = new FormData();

    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach((item, index) => {
            formData.append(`${key}[${index}]`, item);
          });
        } else {
          formData.append(key, value);
        }
      }
    });

    return this.post<T>(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers,
      },
      onUploadProgress: onProgress
        ? (progressEvent: { loaded: number; total?: number }) => {
            const { loaded, total } = progressEvent;
            if (total) {
              onProgress({
                loaded,
                total,
                percent: Math.round((loaded * 100) / total),
              });
            }
          }
        : undefined,
    });
  }

  // ============================================================
  // 文件下载
  // ============================================================

  /**
   * 文件下载
   */
  async download<T = Blob>(
    url: string,
    config?: RequestClientConfig & { method?: 'GET' | 'POST'; data?: any },
  ): Promise<T> {
    const { method = 'GET', data, ...restConfig } = config || {};

    const response = await this.instance.request<T>({
      url,
      method,
      data,
      responseType: 'blob',
      ...restConfig,
    });

    return response.data;
  }

  // ============================================================
  // SSE 流式请求
  // ============================================================

  /**
   * SSE POST 请求
   */
  async postSSE(url: string, data?: any, options?: SseRequestOptions) {
    return this.requestSSE(url, data, { ...options, method: 'POST' });
  }

  /**
   * SSE 请求
   */
  async requestSSE(url: string, data?: any, options?: SseRequestOptions) {
    const baseUrl = this.instance.defaults.baseURL || '';
    const fullUrl = baseUrl ? `${baseUrl.replace(/\/+$/, '')}/${url.replace(/^\/+/, '')}` : url;

    // 构建请求头
    const headers = new Headers();
    headers.set('Accept', 'text/event-stream');
    headers.set('Content-Type', 'application/json');

    // 添加 Token
    if (this.getToken) {
      const endpoint = getEndpointByUrl(url);
      const token = this.getToken(endpoint);
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
    }

    // 合并自定义 headers
    if (options?.headers) {
      new Headers(options.headers).forEach((v, k) => headers.set(k, v));
    }

    // 准备请求体
    let body: BodyInit | null = null;
    if (data && options?.method !== 'GET') {
      body = typeof data === 'string' ? data : JSON.stringify(data);
    }

    const response = await fetch(fullUrl, {
      ...options,
      method: options?.method || 'GET',
      headers,
      body,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No reader available');
    }

    let isEnd = false;
    while (!isEnd) {
      const { done, value } = await reader.read();
      if (done) {
        isEnd = true;
        options?.onEnd?.();
        break;
      }
      const content = decoder.decode(value, { stream: true });
      options?.onMessage?.(content);
    }
  }

  // ============================================================
  // 辅助方法
  // ============================================================

  /** 获取基础 URL */
  getBaseUrl(): string | undefined {
    return this.instance.defaults.baseURL;
  }
}
