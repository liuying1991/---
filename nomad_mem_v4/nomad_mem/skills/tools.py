"""
工具技能 - calculate, datetime, web_search, http_request
"""
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from html.parser import HTMLParser
from nomad_mem.skills.base import BaseSkill


class Calculate(BaseSkill):
    """计算器"""

    @property
    def name(self) -> str:
        return "calculate"

    @property
    def description(self) -> str:
        return "执行数学计算，支持加减乘除、括号、浮点运算。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 '2 + 3 * 4'",
                },
            },
            "required": ["expression"],
        }

    def execute(self, args: dict) -> str:
        expression = args.get("expression", "")

        # 安全过滤：只允许数字和运算符
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "表达式包含非法字符。仅支持数字和+-*/.()"

        try:
            result = eval(expression)  # noqa: S307 - 已做字符过滤
            return f"{expression} = {result}"
        except Exception as e:
            return f"计算错误: {e}"


class GetDatetime(BaseSkill):
    """获取当前日期时间"""

    @property
    def name(self) -> str:
        return "datetime"

    @property
    def description(self) -> str:
        return "获取当前日期和时间。用于回答时间相关的问题。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "时间格式，如 '%Y-%m-%d %H:%M:%S'",
                    "default": "%Y-%m-%d %H:%M:%S",
                },
            },
            "required": [],
        }

    def execute(self, args: dict) -> str:
        fmt = args.get("format", "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        return now.strftime(fmt)


class WebSearch(BaseSkill):
    """网络搜索"""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "使用DuckDuckGo搜索网络信息。用于获取最新知识、新闻、技术文档等。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词",
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数量，默认5",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    def execute(self, args: dict) -> str:
        query = args.get("query", "")
        max_results = args.get("max_results", 5)

        try:
            # 使用DuckDuckGo HTML搜索（无需API key）
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode("utf-8")

            # 简单提取搜索结果
            results = []
            parser = ResultParser()
            parser.feed(html)
            results = parser.results[:max_results]

            if not results:
                return f"未找到'{query}'的搜索结果"

            output = [f"搜索 '{query}':"]
            for i, (title, url, snippet) in enumerate(results, 1):
                output.append(f"{i}. {title}")
                output.append(f"   {url}")
                if snippet:
                    output.append(f"   {snippet}")

            return "\n".join(output)

        except Exception as e:
            return f"搜索错误: {e}"


class ResultParser(HTMLParser):
    """简单HTML解析器，提取搜索结果"""

    def __init__(self):
        super().__init__()
        self.results = []
        self._in_result = False
        self._in_title = False
        self._in_snippet = False
        self._current_title = ""
        self._current_url = ""
        self._current_snippet = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a" and "class" in attrs_dict and attrs_dict.get("class") == "result__snippet":
            self._in_snippet = True
        elif tag == "a" and "href" in attrs_dict:
            href = attrs_dict["href"]
            if href.startswith("http"):
                self._current_url = href
                self._in_title = True


class HttpRequest(BaseSkill):
    """HTTP请求"""

    @property
    def name(self) -> str:
        return "http_request"

    @property
    def description(self) -> str:
        return "发送HTTP请求（GET/POST）。用于访问API或网页内容。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "description": "HTTP方法",
                    "enum": ["GET", "POST"],
                    "default": "GET",
                },
                "url": {
                    "type": "string",
                    "description": "请求URL",
                },
                "headers": {
                    "type": "string",
                    "description": "JSON格式的请求头",
                },
                "body": {
                    "type": "string",
                    "description": "POST请求体",
                },
            },
            "required": ["url"],
        }

    def execute(self, args: dict) -> str:
        method = args.get("method", "GET")
        url = args.get("url", "")
        headers_str = args.get("headers", "{}")
        body = args.get("body", "")

        try:
            headers = json.loads(headers_str) if headers_str else {}
            headers.setdefault("User-Agent", "Jarvis/5.0")

            if method == "POST" and body:
                data = body.encode("utf-8")
            else:
                data = None

            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode("utf-8", errors="replace")

            # 截断过长内容
            if len(content) > 5000:
                content = content[:5000] + f"\n... (截断，共{len(content)}字符)"

            return f"状态码: {response.status}\n{content}"
        except urllib.error.HTTPError as e:
            return f"HTTP错误: {e.code} {e.reason}"
        except Exception as e:
            return f"请求错误: {e}"
