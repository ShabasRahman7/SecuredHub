from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from accounts.permissions import IsAdmin
from core.celery import app as celery_app

class WorkerHealthView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        inspect = celery_app.control.inspect()

        try:
            stats = inspect.stats() or {}
            ping = inspect.ping() or {}
            active = inspect.active() or {}
            reserved = inspect.reserved() or {}
            scheduled = inspect.scheduled() or {}
            active_queues = inspect.active_queues() or {}
        except Exception as exc:  # pragma: no cover - defensive
            return Response(
                {
                    "success": False,
                    "status": "unreachable",
                    "message": "Failed to fetch worker statistics",
                    "error": str(exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        worker_names = sorted(ping.keys())
        workers_online = len(worker_names)

        # derive queue names from active_queues inspection
        queue_names = set()
        for queues in active_queues.values():
            if not queues:
                continue
            for q in queues:
                name = q.get("name")
                if name:
                    queue_names.add(name)

        data = {
            "success": True,
            "status": "healthy" if workers_online > 0 else "no_workers",
            "workers": {
                "online": workers_online,
                "names": worker_names,
                # active / reserved / scheduled counts aggregated across workers
                "active_tasks": sum(len(v or []) for v in active.values()),
                "reserved_tasks": sum(len(v or []) for v in reserved.values()),
                "scheduled_tasks": sum(len(v or []) for v in scheduled.values()),
            },
            "queues": {
                "names": sorted(queue_names),
            },
            # raw stats from Celery (per-worker), useful if you expand UI later
            "raw": {
                "stats": stats,
            },
        }

        return Response(data, status=status.HTTP_200_OK)

