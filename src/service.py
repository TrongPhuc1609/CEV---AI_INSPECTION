"""Operational service loop around the inspection pipeline."""
from __future__ import annotations

from threading import Event
from typing import Callable, Optional


class InspectionService:
    def __init__(self, pipeline, on_inspection: Optional[Callable] = None):
        self.pipeline = pipeline
        self.on_inspection = on_inspection
        self.stop_event = Event()
        self.running = False

    def start(self):
        self.pipeline.start()
        self.running = True
        self.stop_event.clear()

    def stop(self):
        self.stop_event.set()
        if self.running:
            self.pipeline.stop()
        self.running = False

    def run(self, max_products: Optional[int] = None) -> int:
        self.start()
        processed = 0
        try:
            while not self.stop_event.is_set() and (max_products is None or processed < max_products):
                inspection = self.pipeline.run_product()
                processed += 1
                if self.on_inspection:
                    self.on_inspection(inspection)
        finally:
            self.stop()
        return processed
