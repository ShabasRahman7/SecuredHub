import { Link } from 'react-router-dom';
import useWorkerHealth from '../../hooks/useWorkerHealth';

// Small inline loader used while the worker status is being fetched.
const Spinner = () => (
  <div className="flex items-center justify-center py-4">
    <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
  </div>
);

// Compact summary of Celery worker health for the admin dashboard.
const WorkerHealthCard = () => {
  const { data, loading, error, refetch } = useWorkerHealth({ auto: true });

  const status = data?.status || 'unknown';
  const workersOnline = data?.workers?.online ?? 0;
  const activeTasks = data?.workers?.active_tasks ?? 0;
  const queues = data?.queues?.names || [];

  const isHealthy = status === 'healthy' && workersOnline > 0;
  const showSpinner = loading && !data;

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-white/10 p-6 bg-[#0A0F16] shadow-lg lg:col-span-2">
      <div className="flex justify-between items-center">
        <h3 className="text-white text-base font-semibold">Worker Health</h3>
        <Link to="/admin/workers" className="text-primary text-sm font-medium hover:underline">
          View Details
        </Link>
      </div>

      {showSpinner ? (
        <Spinner />
      ) : error ? (
        <div className="flex flex-col items-center gap-2 py-4">
          <p className="text-red-400 text-sm">Failed to load worker status.</p>
          <button onClick={refetch} className="text-primary text-xs hover:underline">
            Retry
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
            <p className="text-gray-300 text-sm">Heartbeat</p>
            <div className="flex items-center gap-2">
              <span
                className={`w-3 h-3 rounded-full ${
                  isHealthy ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                }`}
              />
              <span className={`${isHealthy ? 'text-green-400' : 'text-red-400'} font-medium text-sm`}>
                {isHealthy ? 'OK' : 'Unavailable'}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
            <p className="text-gray-300 text-sm">Online Workers</p>
            <span className="text-white font-medium text-sm">{workersOnline}</span>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
            <p className="text-gray-300 text-sm">Active Tasks</p>
            <span className="text-white font-medium text-sm">{activeTasks}</span>
          </div>

          {/* Queue details are shown on the dedicated Worker Monitoring page; keep the dashboard card focused. */}
        </div>
      )}
    </div>
  );
};

export default WorkerHealthCard;
