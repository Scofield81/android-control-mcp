"""Tool-modulok osszegyujtese. Minden modul egy `register(mcp)` fuggvenyt ad,
amit a szerver inditasakor sorban meghivunk."""

from . import apps, capture, device, files, input as input_tools, system, toggles

REGISTRARS = [
    device.register,
    capture.register,
    input_tools.register,
    apps.register,
    files.register,
    system.register,
    toggles.register,
]
