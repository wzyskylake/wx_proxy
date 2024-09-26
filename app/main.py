import json
from fastapi import FastAPI, Request, Response, Header
import httpx
import logging
import os

app = FastAPI()

# 配置日志
logging.basicConfig(level=logging.INFO)

# 加载服务配置
def load_service_config():
    service_config_str = os.getenv('SERVICE_CONFIG')
    if not service_config_str:
        logging.error("环境变量 'SERVICE_CONFIG' 未设置。")
        return {}
    try:
        services = json.loads(service_config_str)
        logging.info("服务配置从环境变量加载成功。")
        return services
    except json.JSONDecodeError as e:
        logging.error(f"解析服务配置时出错: {e}")
        return {}

SERVICE_CONFIG = load_service_config()

@app.get("/get_openid/")
async def get_openid(x_wx_openid: str = Header(...)):
    # 返回接收到的 openid
    return {"openid": x_wx_openid}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy(request: Request, service: str, path: str):
    target_base_url = SERVICE_CONFIG.get(service)
    if not target_base_url:
        return Response(content=f"未找到服务 '{service}'。", status_code=404)

    # 构建目标 URL
    target_url = f"{target_base_url.rstrip('/')}/{path}"

    # 获取请求参数和头信息
    query_params = dict(request.query_params)
    headers = dict(request.headers)
    body = await request.body()
    headers.pop("host", None)

    headers.setdefault('User-Agent', 'Mozilla/5.0 (compatible; MyProxy/1.0)')

    logging.info(f"服务 '{service}' 的目标基准 URL: {target_base_url}")
    logging.info(f"完整的目标 URL: {target_url}")
    logging.info(f"正在转发 {request.method} 请求到 {target_url}")

    try:
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=query_params,
                content=body,
                timeout=10.0
            )
    except httpx.RequestError as exc:
        logging.error(f"发生错误: {exc}")
        return Response(content=f"请求 {exc.request.url!r} 时发生错误。", status_code=502)

    excluded_headers = ['content-encoding', 'transfer-encoding', 'connection', 'keep-alive']
    response_headers = {key: value for key, value in resp.headers.items() if key.lower() not in excluded_headers}

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
        media_type=resp.headers.get("content-type")
    )
