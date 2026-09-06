"""Tool-modulok osszegyujtese. Minden modul egy `register(mcp)` fuggvenyt ad,
amit a szerver inditasakor sorban meghivunk."""

from . import apps, capture, device, elements, files, rescue, system, toggles, workflows
from . import input as input_tools

REGISTRARS = [
    device.register,
    capture.register,
    input_tools.register,
    elements.register,
    apps.register,
    files.register,
    system.register,
    toggles.register,
    workflows.register,
    rescue.register,
]
