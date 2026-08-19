from src.integration.device_contract import (
    CommissioningDevice,
    DeviceCapabilities,
    DeviceHealth,
    DeviceState,
)


def test_health_ready_is_usable():
    health = DeviceHealth("CAM01", DeviceState.READY, "ok")
    assert health.usable


def test_degraded_device_is_not_usable_for_commissioning():
    health = DeviceHealth("PLC01", DeviceState.DEGRADED, "heartbeat lost")
    assert not health.usable


def test_capability_contract():
    caps = DeviceCapabilities(
        "CAM01",
        "CAMERA",
        vendor="VendorX",
        model="ModelY",
        capabilities=frozenset({"hardware_trigger", "timestamped_frames"}),
    )
    assert caps.supports("hardware_trigger")
    assert not caps.supports("encoder_input")


def test_self_test_defaults_to_health():
    class Device(CommissioningDevice):
        def health(self):
            return DeviceHealth("TRG01", DeviceState.READY, "ok")

        def capabilities(self):
            return DeviceCapabilities("TRG01", "TRIGGER")

    assert Device().self_test().usable
