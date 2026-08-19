"""Vendor-neutral hardware adapters.

These wrappers keep vendor SDKs outside the inspection core.  A real camera,
trigger, lighting controller or PLC implementation can expose its SDK methods
through these callbacks without changing the pipeline or Rule Engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from ..machine_vision.camera.base import Camera, Frame
from ..machine_vision.trigger.base import TriggerEvent, TriggerSource
from ..integration.plc import PLCCommand, PLCInterface


@dataclass
class CallbackCamera(Camera):
    camera_id: str
    open_fn: Callable[[], None]
    close_fn: Callable[[], None]
    capture_fn: Callable[[str, Dict[str, Any]], Any]
    configure_fn: Optional[Callable[[Dict[str, Any]], None]] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    _opened: bool = False
    _counter: int = 0

    def open(self) -> None:
        self.open_fn()
        self._opened = True

    def close(self) -> None:
        if self._opened:
            self.close_fn()
        self._opened = False

    def configure(self, **settings) -> None:
        self.settings.update(settings)
        if self.configure_fn:
            self.configure_fn(dict(self.settings))

    def capture(self) -> Frame:
        if not self._opened:
            raise RuntimeError(f"Camera {self.camera_id} is not open")
        self._counter += 1
        frame_id = f"{self.camera_id}-F{self._counter}"
        image = self.capture_fn(frame_id, dict(self.settings))
        import time
        return Frame(frame_id, image, time.time(), self.camera_id, {"settings": dict(self.settings), "adapter": "CALLBACK"})


@dataclass
class CallbackTrigger(TriggerSource):
    wait_fn: Callable[[], TriggerEvent]

    def wait(self) -> TriggerEvent:
        event = self.wait_fn()
        if not isinstance(event, TriggerEvent):
            raise TypeError("wait_fn must return TriggerEvent")
        return event


@dataclass
class CallbackPLC(PLCInterface):
    send_fn: Callable[[PLCCommand], None]
    commands: list[PLCCommand] = field(default_factory=list)

    def send(self, command: PLCCommand) -> None:
        self.send_fn(command)
        self.commands.append(command)
