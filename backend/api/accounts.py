from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import zipfile
import rarfile
import json
import os
import tempfile

router = APIRouter()

@router.post("/api/accounts/import/files")
async def import_files(files: List[UploadFile] = File(...)):
    """
    批量导入账号文件
    支持：.session, .zip, .rar, .json
    """
    results = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for file in files:
            filename = file.filename
            ext = filename.lower().split('.')[-1]
            
            try:
                # 保存上传的文件
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, 'wb') as f:
                    content = await file.read()
                    f.write(content)
                
                # 处理不同格式
                if ext == 'zip':
                    # 解压 ZIP
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    result = await process_extracted_files(temp_dir)
                    results.extend(result)
                    
                elif ext == 'rar':
                    # 解压 RAR
                    with rarfile.RarFile(file_path, 'r') as rar_ref:
                        rar_ref.extractall(temp_dir)
                    result = await process_extracted_files(temp_dir)
                    results.extend(result)
                    
                elif ext == 'session':
                    # 单个 session 文件
                    result = await process_session_file(file_path, filename)
                    results.append(result)
                    
                elif ext == 'json':
                    # JSON 配置文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    result = await create_account_from_config(config)
                    results.append(result)
                    
            except Exception as e:
                results.append({
                    'filename': filename,
                    'phone': '',
                    'success': False,
                    'message': str(e)
                })
    
    return {'results': results}

async def process_extracted_files(directory):
    """处理解压后的文件"""
    results = []
    session_files = [f for f in os.listdir(directory) if f.endswith('.session')]
    
    for session_file in session_files:
        session_path = os.path.join(directory, session_file)
        json_file = session_file.replace('.session', '.json')
        json_path = os.path.join(directory, json_file)
        
        # 如果有对应的 JSON 配置
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            # 自动生成默认配置
            config = {
                'phone': session_file.replace('.session', ''),
                'api_id': None,
                'api_hash': None
            }
        
        # 读取 session 内容
        with open(session_path, 'rb') as f:
            session_content = f.read()
        
        result = await create_account_with_session(config, session_content)
        results.append(result)
    
    return results

async def process_session_file(file_path, filename):
    """处理单个 session 文件"""
    with open(file_path, 'rb') as f:
        session_content = f.read()
    
    # 自动生成配置
    config = {
        'phone': filename.replace('.session', ''),
        'api_id': None,
        'api_hash': None
    }
    
    return await create_account_with_session(config, session_content)

async def create_account_with_session(config, session_content):
    """使用 session 创建账号"""
    try:
        # TODO: 实际的数据库插入逻辑
        # account = Account.create(**config, session=session_content)
        
        return {
            'filename': config.get('phone', 'unknown') + '.session',
            'phone': config.get('phone'),
            'success': True,
            'message': '导入成功'
        }
    except Exception as e:
        return {
            'filename': config.get('phone', 'unknown') + '.session',
            'phone': config.get('phone'),
            'success': False,
            'message': str(e)
        }

async def create_account_from_config(config):
    """从配置创建账号"""
    try:
        # TODO: 实际的数据库插入逻辑
        return {
            'filename': 'config.json',
            'phone': config.get('phone'),
            'success': True,
            'message': '导入成功'
        }
    except Exception as e:
        return {
            'filename': 'config.json',
            'phone': config.get('phone'),
            'success': False,
            'message': str(e)
        }
