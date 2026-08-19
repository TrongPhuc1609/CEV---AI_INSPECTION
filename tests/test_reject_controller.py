from src.integration.plc import Decision, MockPLC, PLCCommand
from src.integration.reject import RejectController, RejectStatus


def command(decision=Decision.NG):
    return PLCCommand(decision, "P1", "I1", ["MISSING_COMPONENT"])


def test_pass_does_not_issue_reject():
    plc = MockPLC()
    result = RejectController(plc).execute(command(Decision.PASS))
    assert result.status == RejectStatus.NOT_REQUIRED
    assert plc.commands == []


def test_ng_sends_one_reject_command():
    plc = MockPLC()
    result = RejectController(plc).execute(command())
    assert result.status == RejectStatus.SENT
    assert len(plc.commands) == 1
    assert plc.commands[0].decision == Decision.NG


def test_ng_requires_ack_when_ack_adapter_is_configured():
    plc = MockPLC()
    result = RejectController(plc, ack=lambda _cmd, timeout: True).execute(command())
    assert result.status == RejectStatus.ACKNOWLEDGED
    assert result.accepted


def test_reject_ack_timeout_is_not_accepted():
    plc = MockPLC()
    result = RejectController(plc, ack=lambda _cmd, timeout: False).execute(command())
    assert result.status == RejectStatus.TIMEOUT
    assert not result.accepted


def test_missing_identity_fails_closed():
    plc = MockPLC()
    bad = PLCCommand(Decision.NG, "", "I1", ["FAULT"])
    result = RejectController(plc).execute(bad)
    assert result.status == RejectStatus.FAILED
    assert result.reason == "MISSING_IDENTITY"
    assert plc.commands == []


def test_plc_send_exception_fails_closed():
    class BrokenPLC(MockPLC):
        def send(self, command):
            raise RuntimeError("offline")

    result = RejectController(BrokenPLC()).execute(command())
    assert result.status == RejectStatus.FAILED
    assert result.reason.startswith("PLC_SEND_FAILED:")
