from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import httpx
from bs4 import BeautifulSoup
import re
from typing import Optional, Union, List
import asyncio
from prompts import PRESET_PROMPTS

app = FastAPI(title="卡片制作工具 API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContentRequest(BaseModel):
    url: str
    prompt: str
    
    @validator('url')
    def validate_url(cls, v):
        # 验证URL格式
        pattern = re.compile(r'^https?://\S+$')
        if not pattern.match(v):
            raise ValueError('URL必须以http://或https://开头')
        return v

async def fetch_url_with_retry(url: str, max_retries: int = 3, timeout: int = 10):
    """尝试获取URL内容，带重试机制，增加超时时间到10秒"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.text
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            if attempt == max_retries - 1:
                raise HTTPException(status_code=400, detail=f"获取URL内容失败: {str(e)}")
            await asyncio.sleep(1)  # 重试前等待1秒

def extract_main_content(html_content: str) -> str:
    """增强版内容提取算法"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除常见的广告和无关元素
    for tag in soup.find_all(['script', 'style', 'iframe', 'nav', 'footer', 'ads', 'header']):
        tag.decompose()
    
    # 提取正文内容 (使用更复杂的策略)
    main_content = ""
    
    # 1. 首先尝试寻找最可能的内容容器
    potential_containers = []
    
    # 尝试多种选择器寻找内容区域
    selectors = [
        'article', 'main', '.content', '.article', '.post', '#content', '#article', '#main',
        '[class*="article"]', '[class*="content"]', '[class*="post"]', '.post-content', '.entry-content'
    ]
    
    for selector in selectors:
        try:
            elements = soup.select(selector)
            potential_containers.extend(elements)
        except:
            continue
    
    # 如果找到了潜在容器
    if potential_containers:
        # 选择内容最长的容器
        main_container = max(potential_containers, key=lambda x: len(x.get_text(strip=True)))
        # 提取段落
        paragraphs = main_container.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
    else:
        # 如果找不到明确的内容区域，就获取所有段落
        paragraphs = soup.find_all(['p', 'div'])
    
    # 进一步过滤和提取内容
    content_texts = []
    for p in paragraphs:
        text = p.get_text(strip=True)
        if len(text) > 15 and '广告' not in text and not re.match(r'^[0-9.]*$', text):
            content_texts.append(text)
    
    # 如果上面方法提取的内容太少，尝试使用更宽松的方法
    if len('\n'.join(content_texts)) < 100:
        # 移除所有空白文本
        texts = [node.strip() for node in soup.stripped_strings]
        # 过滤短句和特殊内容
        content_texts = [t for t in texts if len(t) > 15 and not re.match(r'^[0-9.]*$', t)]
    
    return '\n'.join(content_texts)

@app.post("/process_content")
async def process_content(data: ContentRequest):
    """
    主要处理流程:
    1. 验证URL有效性
    2. 智能内容提取
    3. 拼接模板
    """
    try:
        # 获取URL内容
        html_content = await fetch_url_with_retry(data.url)
        
        # 提取主要内容
        main_content = extract_main_content(html_content)
        
        if not main_content or len(main_content.strip()) < 30:
            return {"result": f"[{data.prompt}] 请参考以下内容：无法从该URL提取有效内容"}
        
        # 拼接结果
        result = f"[{data.prompt}] 请参考以下内容：{main_content}"
        
        return {"result": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@app.post("/process_html_file")
async def process_html_file(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    """
    处理上传的HTML文件:
    1. 解析HTML文件内容
    2. 提取主要内容
    3. 拼接模板
    """
    try:
        # 验证文件类型
        if not file.filename.endswith(('.html', '.htm')):
            raise HTTPException(status_code=400, detail="只支持HTML格式文件")
        
        # 读取文件内容
        html_content = await file.read()
        html_text = html_content.decode('utf-8', errors='ignore')
        
        # 提取主要内容
        main_content = extract_main_content(html_text)
        
        if not main_content or len(main_content.strip()) < 30:
            return {"result": f"[{prompt}] 请参考以下内容：无法从该HTML文件提取有效内容"}
        
        # 拼接结果
        result = f"[{prompt}] 请参考以下内容：{main_content}"
        
        return {"result": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理HTML文件失败: {str(e)}")

@app.get("/preset_prompts")
async def get_preset_prompts():
    """
    获取预设提示词列表
    
    返回:
    - 预设提示词数组
    """
    return {"prompts": PRESET_PROMPTS}

@app.get("/")
def read_root():
    return {"message": "卡片制作工具API服务正常运行"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)