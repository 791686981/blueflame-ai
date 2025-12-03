"""
工具模块（惰性导出，避免导入时的副作用）。

说明：不在此处导入任何具体子模块，避免例如 Amap stdio 服务器在导入阶段启动。
使用示例：
    from agent_service.tools import weather  # 触发 __getattr__ 惰性加载
    # 或精确导入子模块（推荐，副作用更可控）：
    from agent_service.tools.weather import weather
"""

from typing import Any

__all__ = [
    # 工具变量（按需懒加载）
    "amap_maps",
    "time_tools",
    "antv_visualization_chart",
    "bidding_tenders",
    "tendency_software",
    "enterprise_registry",
    "weather",
    "aviation",
    "railway_12306",
    "web_search",
    "bidding_full",
    "supplier_management",
    "enterprise_bigdata",
    "enterprise_risk",
    "gourmet_guide",
    "bidsearch",
]


def __getattr__(name: str) -> Any:
    mapping = {
        "amap_maps": (".amap_maps", "amap_maps"),
        "time_tools": (".time_tools", "time_tools"),
        "antv_visualization_chart": (".antv_visualization_chart", "antv_visualization_chart"),
        "bidding_tenders": (".bidding_tenders", "bidding_tenders"),
        "tendency_software": (".tendency_software", "tendency_software"),
        "enterprise_registry": (".enterprise_registry", "enterprise_registry"),
        "weather": (".weather", "weather"),
        "aviation": (".aviation", "aviation"),
        "railway_12306": (".railway_12306", "railway_12306"),
        "web_search": (".web_search", "web_search"),
        "bidding_full": (".bidding_full", "bidding_full"),
        "supplier_management": (".supplier_management", "supplier_management"),
        "enterprise_bigdata": (".enterprise_bigdata", "enterprise_bigdata"),
        "enterprise_risk": (".enterprise_risk", "enterprise_risk"),
        "gourmet_guide": (".gourmet_guide", "gourmet_guide"),
        "bidsearch": (".bidsearch", "bidsearch"),
    }
    if name in mapping:
        mod_name, attr = mapping[name]
        from importlib import import_module

        mod = import_module(f"{__name__}{mod_name}")
        return getattr(mod, attr)
    raise AttributeError(f"module 'agent_service.tools' has no attribute {name!r}")
