import { useState, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import useWorkerHealth from '../../hooks/useWorkerHealth';

// Reusable loading spinner sized for buttons or panels.
const Spinner = ({ size = 'md' }) => {
  const sizeClass = size === 'sm' ? 'w-4 h-4' : 'w-8 h-8';
  return <div className={`${sizeClass} border-2 border-primary border-t-transparent rounded-full animate-spin`} />;
};

// Detailed page for inspecting Celery worker status, tasks, and queues.
const WorkerMonitoring = () => {
  const { data, loading, error, refetch } = useWorkerHealth({ auto: false });
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    if (data) {
      setLastUpdate(new Date());
    }
  }, [data]);

  const workers = data?.workers || {};
  const queues = data?.queues?.names || [];
  const status = data?.status || 'unknown';

  const statusColor =
    status === 'healthy'
      ? 'text-green-400'
      : status === 'no_workers'
      ? 'text-yellow-400'
      : 'text-red-400';

  return (
    <>
      <div className="flex flex-col sm:flex-row justify-between gap-4 items-start sm:items-center mb-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-white text-2xl sm:text-3xl font-black leading-tight tracking-tight">
            Worker Monitoring
          </h1>
          <p className="text-gray-400 text-sm sm:text-base font-normal leading-normal">
            Observe Celery worker health, active tasks, and queues.
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdate && (
            <span className="text-gray-400 text-sm">
              Last update: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={refetch}
            disabled={loading}
            className="btn btn-primary h-10 px-4 rounded-lg text-sm font-medium gap-2 hover:shadow-lg border-none flex items-center"
          >
            {loading ? <Spinner size="sm" /> : <RefreshCw className="w-4 h-4" />}
            Refresh
          </button>
        </div>
      </div>

      {error && !data ? (
        <p className="text-red-400 text-sm mb-4">
          Failed to load worker metrics. Check worker/rabbitmq containers.
        </p>
      ) : !data ? (
        <p className="text-gray-400 text-sm">Click Refresh to load worker status.</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="rounded-xl border border-white/10 p-6 bg-[#0A0F16]">
            <h2 className="text-white text-sm font-semibold mb-4">Workers</h2>
            <div className="space-y-2 text-sm text-gray-300">
              <div className="flex justify-between">
                <span>Status</span>
                <span className={`font-semibold ${statusColor}`}>{status}</span>
              </div>
              <div className="flex justify-between">
                <span>Online</span>
                <span className="font-medium">{workers.online ?? 0}</span>
              </div>
              <div>
                <p className="text-gray-400 text-xs mb-1">Names</p>
                <p className="text-xs text-gray-200 break-all">
                  {workers.names?.length ? workers.names.join(', ') : 'No workers detected'}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-white/10 p-6 bg-[#0A0F16]">
            <h2 className="text-white text-sm font-semibold mb-4">Tasks</h2>
            <div className="space-y-2 text-sm text-gray-300">
              <div className="flex justify-between">
                <span>Active</span>
                <span className="font-medium">{workers.active_tasks ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Reserved</span>
                <span className="font-medium">{workers.reserved_tasks ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Scheduled</span>
                <span className="font-medium">{workers.scheduled_tasks ?? 0}</span>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-white/10 p-6 bg-[#0A0F16]">
            <h2 className="text-white text-sm font-semibold mb-4">Queues</h2>
            <div className="space-y-2 text-sm text-gray-300">
              <p className="text-xs text-gray-200">
                {queues.length ? queues.join(', ') : 'No active queues detected'}
              </p>
              <p className="text-xs text-gray-500">
                Queue depth is not yet displayed; RabbitMQ management metrics can be wired in later.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default WorkerMonitoring;
