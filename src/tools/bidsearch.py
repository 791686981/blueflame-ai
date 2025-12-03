"""标讯查询相关的原生 LangChain 工具（独立于 BidSage）。

提供三个工具：
- bid_list：按关键词/区域等过滤检索标讯列表，支持 CSV 达阈值自动上传 COS。
- bid_detail：根据标讯 ID 拉取详情。
- bid_radar：多关键词、跨天数扫描并可去重，同样支持 CSV 上传。

必需环境变量：
- JIANYU_APPID / JIANYU_KEY

可选环境变量（保持与旧实现一致）：
- JIANYU_BASE_URL（默认 https://api.jianyu360.com/data/biddata）
- COS_REGION / COS_BUCKET / COS_SECRET_ID / COS_SECRET_KEY（全部提供才启用 CSV 上传）
- COS_BASE_URL（可选，用于生成可直接访问的 URL）
- CSV_EXPORT_THRESHOLD（默认 50）
- CSV_LIFECYCLE_DAYS（默认 7）
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
from datetime import datetime
from tempfile import NamedTemporaryFile
import time
from typing import Any, Dict, List, Mapping, Optional, Sequence

import requests
from langchain.tools import tool

from .registry import get_tools, get_tools_async, register_callable_tool

logger = logging.getLogger(__name__)

_TOOL_NAME = "bidsearch"
_DEFAULT_BASE_URL = "https://api.jianyu360.com/data/biddata"
_DEFAULT_SCOPE = "公告标题,公告正文,标的物,项目名称"
_DEFAULT_SUBTYPES = (
    "拟建,采购意向,预告,预审,预审结果,论证意见,需求公示,招标,询价,竞谈,"
    "单一,竞价,变更,邀标,成交,中标,废标,流标,结果变更,合同,违规,验收,其它"
)
_CSV_EXPORT_THRESHOLD = int(os.getenv("CSV_EXPORT_THRESHOLD", "50"))
_CSV_LIFECYCLE_DAYS = int(os.getenv("CSV_LIFECYCLE_DAYS", "7"))
_COS_BASE_URL = os.getenv("COS_BASE_URL", "").rstrip("/")


# ------------------ 内部客户端 ------------------


class _JianyuClient:
    def __init__(self) -> None:
        self.appid = os.getenv("JIANYU_APPID", "")
        self.key = os.getenv("JIANYU_KEY", "")
        if not self.appid or not self.key:
            raise RuntimeError("缺少剑鱼 API 凭证：请设置 JIANYU_APPID / JIANYU_KEY")
        self.base_url = os.getenv("JIANYU_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")

    @staticmethod
    def _token(appid: str, key: str, timestamp: Optional[str] = None) -> tuple[str, str]:
        ts = timestamp or str(int(time.time()))
        token = hashlib.md5(f"{appid}{ts}{key}".encode("utf-8")).hexdigest().upper()
        return token, ts

    def _post(self, path: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = requests.post(
                url,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json;charset=utf-8"},
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            return {"code": -1, "msg": f"请求失败: {exc}", "data": [], "count": 0}

    def bid_list(self, **filters: Any) -> Dict[str, Any]:
        token, ts = self._token(self.appid, self.key)
        payload = {"appid": self.appid, "token": token, "timestamp": ts, "key": self.key, **filters}
        return self._post("list", payload)

    def bid_info(self, bid_id: str) -> Dict[str, Any]:
        token, ts = self._token(self.appid, self.key)
        payload = {"appid": self.appid, "token": token, "timestamp": ts, "key": self.key, "id": bid_id}
        return self._post("info", payload)


def _time_range(days: int) -> tuple[int, int]:
    end_ts = int(time.time())
    start_ts = end_ts - max(days, 1) * 86400
    return start_ts, end_ts


# ------------------ CSV 导出到腾讯云 COS ------------------

try:  # pragma: no cover - 依赖外部包
    from qcloud_cos import CosConfig, CosS3Client  # type: ignore
except ImportError:  # pragma: no cover
    CosConfig = None
    CosS3Client = None


class _CSVExporter:
    """最小化的 CSV → COS 上传器（与旧逻辑保持一致）。"""

    def __init__(self) -> None:
        if not all(
            [
                os.getenv("COS_REGION"),
                os.getenv("COS_BUCKET"),
                os.getenv("COS_SECRET_ID"),
                os.getenv("COS_SECRET_KEY"),
            ]
        ):
            raise RuntimeError("未配置 COS，无法导出 CSV")
        if not CosConfig or not CosS3Client:
            raise ImportError("缺少 qcloud_cos 依赖，请先安装 cos-python-sdk-v5")

        self.bucket = os.getenv("COS_BUCKET", "")
        self.base_url = _COS_BASE_URL
        self.client = CosS3Client(
            CosConfig(
                Region=os.getenv("COS_REGION", ""),
                SecretId=os.getenv("COS_SECRET_ID", ""),
                SecretKey=os.getenv("COS_SECRET_KEY", ""),
                Token=None,
            )
        )

    def export(self, records: List[Dict[str, Any]], *, key_prefix: str) -> Dict[str, Any]:
        if not records:
            raise ValueError("没有可导出的数据")

        fieldnames = sorted({key for record in records for key in record.keys()})
        if not fieldnames:
            raise ValueError("记录中缺少字段，无法生成 CSV")

        with NamedTemporaryFile("w+", newline="", encoding="utf-8", delete=False) as tmp:
            writer = csv.DictWriter(tmp, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(
                    {
                        key: json.dumps(record.get(key), ensure_ascii=False)
                        if isinstance(record.get(key), (dict, list, tuple))
                        else ("" if record.get(key) is None else record.get(key))
                        for key in fieldnames
                    }
                )
            tmp_path = tmp.name

        key = f"{key_prefix.rstrip('/')}/{datetime.utcnow():%Y%m%d-%H%M%S}.csv"
        try:
            with open(tmp_path, "rb") as fh:
                self.client.put_object(
                    Bucket=self.bucket,
                    Body=fh,
                    Key=key,
                    ContentType="text/csv",
                    ACL="public-read",
                )
        finally:
            os.remove(tmp_path)

        url = f"{self.base_url}/{key}" if self.base_url else key
        return {
            "key": key,
            "url": url,
            "record_count": len(records),
            "expires_in_days": _CSV_LIFECYCLE_DAYS,
        }


_csv_exporter: Optional[_CSVExporter] = None
_csv_init_failed = False


def _get_csv_exporter() -> Optional[_CSVExporter]:
    global _csv_exporter, _csv_init_failed
    if _csv_init_failed:
        return None
    if _csv_exporter is not None:
        return _csv_exporter
    try:
        _csv_exporter = _CSVExporter()
        return _csv_exporter
    except Exception as exc:  # pragma: no cover - 初始化失败时仅记录
        logger.warning("初始化 CSV 导出器失败: %s", exc)
        _csv_init_failed = True
        return None


def _export_csv(records: List[Dict[str, Any]], key_prefix: str) -> Optional[Dict[str, Any]]:
    exporter = _get_csv_exporter()
    if not exporter:
        return None
    try:
        return exporter.export(records, key_prefix=key_prefix)
    except Exception as exc:  # pragma: no cover
        logger.error("CSV 导出失败: %s", exc)
        return {"error": str(exc)}


# ------------------ LangChain 工具 ------------------


@tool("bid_list", description="按关键词/区域等条件检索标讯列表。")
def bid_list(
    keyword: str,
    *,
    days: int = 7,
    area: Optional[str] = None,
    buyerclass: Optional[str] = None,
    industry: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    keywordScope: Optional[str] = None,
    subType: Optional[str] = None,
) -> Dict[str, Any]:
    """
    参数:
        keyword: 关键词，支持逗号分隔多个。
        days: 向前回溯的天数（发布起止时间自动计算）。
        area / buyerclass / industry: 可选过滤条件。
        page / size: 翻页参数，传递给剑鱼 list 接口。
        keywordScope / subType: 覆盖默认匹配范围与子类型。
    返回:
        与剑鱼 list 接口一致的字典，包含 code/msg/data/count 等字段。
    """
    client = _JianyuClient()
    start_ts, end_ts = _time_range(days)
    filters: Dict[str, Any] = {
        "keyword": keyword,
        "keywordScope": keywordScope or _DEFAULT_SCOPE,
        "subType": subType or _DEFAULT_SUBTYPES,
        "publishtimeStart": start_ts,
        "publishtimeEnd": end_ts,
        "page": page,
        "size": size,
    }
    for k, v in {"area": area, "buyerclass": buyerclass, "industry": industry}.items():
        if v is not None:
            filters[k] = v
    resp = client.bid_list(**filters)
    records = resp.get("data") or []
    if resp.get("code", 0) == 0 and len(records) >= _CSV_EXPORT_THRESHOLD:
        csv_info = _export_csv(records, key_prefix="biddata")
        if csv_info:
            resp["csv"] = csv_info
            if "error" not in csv_info:
                resp["summary"] = {
                    "total": resp.get("count", len(records)),
                    "keyword": keyword,
                    "days": days,
                    "page": page,
                    "size": size,
                }
                resp["data"] = []
    return resp


@tool("bid_detail", description="根据标讯 ID 获取详情。")
def bid_detail(bid_id: str) -> Dict[str, Any]:
    """
    参数:
        bid_id: 标讯唯一 ID。
    返回:
        剑鱼 info 接口的响应字典。
    """
    client = _JianyuClient()
    return client.bid_info(bid_id)


@tool("bid_radar", description="多关键词、跨天数扫描标讯，自动去重。")
def bid_radar(
    keywords: Sequence[str] | str,
    *,
    days: int = 7,
    maxItems: Optional[int] = None,
    dedupe: bool = True,
) -> Dict[str, Any]:
    """
    参数:
        keywords: 字符串（可用逗号分隔）或字符串列表。
        days: 向前回溯的天数。
        maxItems: 最多返回多少条，None 表示不限。
        dedupe: 是否按标讯 ID 去重。
    返回:
        {success, message, total, data, keywords, days, deduped}
    """
    client = _JianyuClient()
    if isinstance(keywords, str):
        kw_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
    else:
        kw_list = [kw.strip() for kw in keywords if kw.strip()]
    if not kw_list:
        return {"success": False, "message": "至少需要一个关键词", "data": [], "total": 0}

    start_ts, end_ts = _time_range(days)
    seen_ids = set()
    results: List[Dict[str, Any]] = []

    for kw in kw_list:
        next_token: Optional[str] = None
        while True:
            payload = {
                "keyword": kw,
                "keywordScope": _DEFAULT_SCOPE,
                "subType": _DEFAULT_SUBTYPES,
                "publishtimeStart": start_ts,
                "publishtimeEnd": end_ts,
            }
            if next_token:
                payload["next"] = next_token

            resp = client.bid_list(**payload)
            data = resp.get("data") or []
            if resp.get("code", 0) != 0 or not data:
                break

            for item in data:
                item_id = item.get("id")
                if dedupe and item_id:
                    if item_id in seen_ids:
                        continue
                    seen_ids.add(item_id)
                item = dict(item)
                item["search_keyword"] = kw
                results.append(item)
                if maxItems and len(results) >= maxItems:
                    break
            if maxItems and len(results) >= maxItems:
                break

            next_token = resp.get("next")
            if not next_token:
                break
        if maxItems and len(results) >= maxItems:
            break

    payload = {
        "success": True,
        "message": f"获取 {len(results)} 条记录",
        "total": len(results),
        "data": results,
        "keywords": kw_list,
        "days": days,
        "deduped": dedupe,
    }
    if len(results) >= _CSV_EXPORT_THRESHOLD:
        csv_info = _export_csv(results, key_prefix="radar")
        if csv_info:
            payload["csv"] = csv_info
            if "error" not in csv_info:
                payload["summary"] = {
                    "total": len(results),
                    "keywords": kw_list,
                    "days": days,
                    "deduped": dedupe,
                }
                payload["data"] = []
    return payload


# ------------------ 注册与导出 ------------------


def _build_tools() -> List[Any]:
    return [bid_list, bid_detail, bid_radar]


register_callable_tool(
    _TOOL_NAME,
    builder=_build_tools,
    description="标讯查询工具集合：列表检索、详情、雷达扫描（支持 CSV 上传 COS）。",
    tags=("bidding", "jianyu", "python"),
)


async def get_bidsearch_tools_async(*, refresh: bool = False) -> List[Any]:
    return await get_tools_async(_TOOL_NAME, refresh=refresh)


def get_bidsearch_tools(*, refresh: bool = False) -> List[Any]:
    return get_tools(_TOOL_NAME, refresh=refresh)


bidsearch: List[Any] = get_bidsearch_tools()


if __name__ == "__main__":  # pragma: no cover
    import asyncio

    tools = asyncio.run(get_bidsearch_tools_async())
    print(f"获取到 {len(tools)} 个标讯工具")
