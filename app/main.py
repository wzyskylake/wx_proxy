from fastapi import FastAPI, Request, HTTPException
import httpx
from pydantic import BaseModel
from typing import Optional, Dict

app = FastAPI()

# 定义请求体模型
class ProxyRequest(BaseModel):
    url: str
    method: str = "POST"  # 默认使用POST方法
    headers: Optional[Dict[str, str]] = {"Content-Type": "application/json"}  # 默认Content-Type为application/json
    body: Optional[dict] = None  # GET请求时，body可以为空

# 定义跳板API，转发请求到外部API
@app.post("/proxy")
async def forward_to_api(proxy_request: ProxyRequest):
    url = proxy_request.url
    method = proxy_request.method.upper()
    headers = proxy_request.headers
    body = proxy_request.body

    try:
        async with httpx.AsyncClient() as client:
            if method == "POST":
                # 转发 POST 请求
                response = await client.post(url, headers=headers, json=body)
            elif method == "GET":
                # 转发 GET 请求
                response = await client.get(url, headers=headers, params=body)
            elif method == "PUT":
                # 转发 PUT 请求
                response = await client.put(url, headers=headers, json=body)
            elif method == "DELETE":
                # 转发 DELETE 请求
                response = await client.delete(url, headers=headers, json=body)
            else:
                raise HTTPException(status_code=405, detail="Unsupported HTTP method")
            
            response.raise_for_status()

            # 将外部API的响应直接返回给客户端
            return response.json()

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"External API error: {e.response.text}") from e
