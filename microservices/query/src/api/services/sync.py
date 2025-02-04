# src/api/services/sync.py
from datetime import datetime
from typing import Dict, List
from fastapi import HTTPException
from fastapi.logger import logger
from sqlalchemy import and_, insert, select
from sqlalchemy.exc import SQLAlchemyError
import httpx
from config import get_settings
from api.models.service import ServiceInstance
from api.models.interest import RegionInterest, TimeInterest
from api.dependencies.database import get_db


setting=get_settings()
class SyncService:
    def __init__(self):
        self.gateway_url = setting.api_gateway
        self.collector_data_endpoints = {
            "region": "/interests/region-interests",
            "time": "/interests/time-interests"
        }

    async def fetch_collectors(self):
        """筛选trends_collector服务实例"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f'{self.gateway_url}/_internal/services')
                response.raise_for_status()
                
                # 过滤健康且服务名匹配的实例
                return [
                    instance for instance in response.json()['services']["trends_collector"]
                    if instance["service_name"] == "trends_collector"
                    and instance["is_healthy"]
                ]
        except Exception as e:
            logger.error(f"获取collector服务失败: {str(e)}")
            raise HTTPException(500, "无法获取collector服务列表")

    async def _sync_collector_data(self, instance: ServiceInstance):
        """同步单个collector实例数据"""
        base_url = f"http://{instance['host']}:{instance['port']}"
        
        async with httpx.AsyncClient(
            base_url=base_url,
            timeout=30  # 增加超时时间
        ) as client:
            # 先检查健康状态
            try:
                health_check = await client.get(instance["health_check_url"])
                if not health_check.is_success:
                    logger.warning(f"实例 {instance['instance_id']} 不健康，跳过同步")
                    return
            except Exception as e:
                logger.error(f"健康检查失败: {str(e)}")
                return

            # 执行数据同步
            await self._sync_data_type(client, "region", RegionInterest)
            await self._sync_data_type(client, "time", TimeInterest)
            
    async def sync_all_data(self):
        """主同步方法"""
        collectors = await self.fetch_collectors()
        for collector in collectors:
            await self._sync_collector_data(collector)

    async def _sync_data_type(self, client, data_type: str, model):
        """使用分页插件后的同步逻辑"""
        endpoint = self.collector_data_endpoints[data_type]
    
        async for batch in self._paginated_fetch(client, endpoint):
            await self._batch_insert(model, batch, data_type)
            
    async def _paginated_fetch(self, client, endpoint: str):
        """适配自定义分页格式的生成器"""
        page = 1
        per_page = 1000  # 与collector服务的最大分页大小一致
    
        while True:
            try:
                params = {"pageNumber": page, "pageSize": per_page}
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
            
                data = response.json()
                yield data["items"]
            
                if page >= data["pages"]:
                    break
                page += 1

            except Exception as e:
                logger.error(f"分页获取失败: {str(e)}")
                break

    async def _batch_insert(self, model, batch: List[Dict], data_type: str):
        """通用批量插入冲突处理"""
        db = next(get_db())
        try:
            # 获取数据库方言
            dialect = db.bind.dialect.name

            # 定义唯一约束字段
            conflict_elements = (
                ["keyword", "geo_code", "timeframe_start", "timeframe_end"]
                if data_type == "region" 
                else ["keyword", "time", "geo_code"]
            )
            batch = [
                    {k: datetime.strptime(v, "%Y-%m-%d") if k in ["timeframe_start", "timeframe_end", "time"] else v 
                     for k, v in item.items()} for item in batch
                    ]
            # 构造基础插入语句
            stmt = insert(model).values(batch)

            # 方言特定处理
            if dialect == "postgresql":
                stmt = stmt.on_conflict_do_nothing(index_elements=conflict_elements)
            elif dialect == "sqlite":
                stmt = stmt.prefix_with("OR IGNORE")
            elif dialect == "mysql":
                # 需要创建唯一索引，自动忽略重复
                stmt = stmt.prefix_with("IGNORE")
            else:
                # 通用回退方案：先删除可能冲突的记录
                existing = db.execute(
                    select(model).where(and_(
                        getattr(model, col) == item[col]
                        for col in conflict_elements
                        for item in batch
                    ))
                )
                db.delete(existing.scalars())

            db.execute(stmt)
            db.commit()
            logger.debug(f"成功插入{len(batch)}条数据")

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"批次插入失败: {str(e)}")
            # 降级为逐条插入
            await self._insert_one_by_one(db, model, batch, conflict_elements)
        finally:
            db.close()
    async def _insert_one_by_one(self, db, model, batch, conflict_fields):
        """降级方案：逐条插入处理"""
        success = 0
        for item in batch:
            try:
                stmt = insert(model).values(**item)
                # 使用存在性检查
                exists = await db.execute(
                    select(model).where(and_(
                        getattr(model, field) == item[field]
                        for field in conflict_fields
                    ))
                )
                if not exists.scalars().first():
                    await db.execute(stmt)
                    await db.commit()
                    success += 1
            except Exception as e:
                await db.rollback()
                logger.warning(f"单条插入失败: {str(e)}")
        logger.info(f"降级插入成功{success}/{len(batch)}条")