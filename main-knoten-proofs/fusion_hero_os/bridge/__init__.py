"""Fusion Hero OS Bridge — IPC Gateway + Module Router."""

from fusion_hero_os.bridge.gateway import IPCGateway, get_ipc_gateway
from fusion_hero_os.bridge.router import handle_ipc_message, route_dispatch

__all__ = ["IPCGateway", "get_ipc_gateway", "handle_ipc_message", "route_dispatch"]