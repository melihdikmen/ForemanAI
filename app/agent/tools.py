"""Agent tool registry: the callables plus their JSON schemas for the LLM.

TOOL_SCHEMAS is what we send to the model (so it knows each tool's name and
parameters). TOOL_FUNCTIONS maps a tool name to the Python function we actually run.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.tools.faults import get_fault_history
from app.tools.manuals import search_manuals
from app.tools.work_orders import draft_work_order

# name -> python callable
TOOL_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "search_manuals": search_manuals,
    "get_fault_history": get_fault_history,
    "draft_work_order": draft_work_order,
}

# OpenAI-style tool schemas describing each tool to the model.
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_manuals",
            "description": "Makine kılavuzlarında arama yapar; arıza giderme, bakım ve "
            "güvenlik adımları için ilgili kılavuz parçalarını kaynaklarıyla döndürür.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Aranacak metin (ör. 'E-102 yağ sıcaklığı').",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fault_history",
            "description": "Geçmiş arıza kayıtlarının salt-okunur özeti. 'Kaç kez', "
            "'toplam duruş', 'en çok arıza', 'kaç kritik' gibi sayısal sorular için.",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_code": {
                        "type": "string",
                        "description": "Makine kodu, ör. 'PRES-3' (boş = tüm makineler).",
                    },
                    "since_months": {
                        "type": "integer",
                        "description": "Son N ay (boş = tüm zamanlar).",
                    },
                    "alarm_code": {"type": "string", "description": "Alarm kodu, ör. 'E-102'."},
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Önem derecesi filtresi.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_work_order",
            "description": "İş emri TASLAĞI oluşturur (veritabanına yazmaz). Teknisyen bir iş emri "
            "istediğinde kullanılır; taslak ustabaşı onayına sunulur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_code": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "proposed_actions": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                },
                "required": ["machine_code", "title", "description", "proposed_actions"],
            },
        },
    },
]
