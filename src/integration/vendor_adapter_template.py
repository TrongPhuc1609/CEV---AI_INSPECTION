"""Template for wiring a real vendor SDK into the inspection core.

Copy this module into a site/vendor integration package and replace the
callbacks with the selected camera, trigger/encoder, lighting and PLC SDK.
Do not import vendor SDKs into src/production_pipeline.py or the Rule Engine.
"""
from __future__ import annotations

from .hardware_adapters import CallbackCamera, CallbackPLC, CallbackTrigger, HardwareFactory


class SiteHardwareFactory(HardwareFactory):
    def __init__(self, camera_sdk, trigger_sdk, lighting_sdk, plc_sdk):
        self.camera_sdk = camera_sdk
        self.trigger_sdk = trigger_sdk
        self.lighting_sdk = lighting_sdk
        self.plc_sdk = plc_sdk

    def camera(self, camera_config):
        sdk = self.camera_sdk
        return CallbackCamera(
            camera_id=camera_config.camera_id,
            open_fn=sdk.open,
            close_fn=sdk.close,
            configure_fn=sdk.configure,
            capture_fn=sdk.capture,
        )

    def trigger(self, trigger_config):
        # sdk.wait() MUST return src.machine_vision.trigger.base.TriggerEvent
        # containing product_id, timestamp, position and (when available)
        # velocity_units_per_s in metadata.
        return CallbackTrigger(wait_fn=self.trigger_sdk.wait)

    def lighting(self, lighting_config):
        # Adapt the vendor light controller to the existing LightingController
        # contract. Keep vendor-specific commands in this module only.
        from ..machine_vision.lighting.controller import LightingController

        controller = LightingController()
        original_apply = controller.apply

        def apply(profile):
            self.lighting_sdk.apply(profile)
            original_apply(profile)

        controller.apply = apply
        return controller

    def plc(self, plc_config):
        # sdk.send(command) MUST map PASS/NG to the real PLC handshake and
        # remain observable during commissioning (CallbackPLC records commands).
        return CallbackPLC(send_fn=self.plc_sdk.send)
