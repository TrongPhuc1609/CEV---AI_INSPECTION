from src.service import InspectionService


class DummyPipeline:
    def __init__(self): self.started = 0; self.stopped = 0; self.runs = 0
    def start(self): self.started += 1
    def stop(self): self.stopped += 1
    def run_product(self): self.runs += 1; return self.runs


def test_service_runs_bounded_loop_and_stops_cleanly():
    pipeline = DummyPipeline()
    seen = []
    service = InspectionService(pipeline, seen.append)
    assert service.run(max_products=3) == 3
    assert pipeline.started == 1
    assert pipeline.stopped == 1
    assert seen == [1, 2, 3]
    assert not service.running
