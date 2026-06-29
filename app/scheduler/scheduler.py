from __future__ import annotations


class LeetbitScheduler:
    def __init__(self, workflow, interval_seconds: int) -> None:
        self.workflow = workflow
        self.interval_seconds = interval_seconds
        self._scheduler = None

    def _ensure_scheduler(self):
        if self._scheduler is None:
            from apscheduler.schedulers.background import BackgroundScheduler

            self._scheduler = BackgroundScheduler(timezone="UTC")
        return self._scheduler

    def start(self) -> None:
        scheduler = self._ensure_scheduler()
        if scheduler.running:
            return
        scheduler.add_job(
            self.workflow.run_once,
            trigger="interval",
            seconds=self.interval_seconds,
            id="leetbit.poll-submissions",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
        scheduler.start()

    def shutdown(self) -> None:
        if self._scheduler is not None and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
