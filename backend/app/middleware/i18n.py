"""
国际化中间件

根据请求的 Accept-Language 头或查询参数设置当前请求的语言
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.i18n import parse_accept_language, set_locale


class I18nMiddleware(BaseHTTPMiddleware):
    """
    国际化中间件
    
    语言检测优先级：
    1. 查询参数 ?lang=zh_CN
    2. 请求头 X-Language
    3. 请求头 Accept-Language
    4. 默认语言
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 1. 尝试从查询参数获取
        lang = request.query_params.get("lang")
        
        # 2. 尝试从 X-Language 头获取
        if not lang:
            lang = request.headers.get("X-Language")
        
        # 3. 尝试从 Accept-Language 头解析
        if not lang:
            accept_language = request.headers.get("Accept-Language")
            lang = parse_accept_language(accept_language)
        
        # 设置当前请求的语言
        if lang:
            set_locale(lang)
        
        response = await call_next(request)
        
        # 在响应头中返回当前使用的语言
        from app.core.i18n import get_locale
        response.headers["Content-Language"] = get_locale()
        
        return response
