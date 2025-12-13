import { Link } from 'react-router-dom';

const WorkerHealthCard = () => {
    return (
        <div className="flex flex-col gap-4 rounded-xl border border-white/10 p-6 bg-[#0A0F16] shadow-lg lg:col-span-2">
            <div className="flex justify-between items-center">
                <h3 className="text-white text-base font-semibold">Worker Health</h3>
                <Link to="/admin/workers" className="text-primary text-sm font-medium hover:underline">View Details</Link>
            </div>
            <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
                    <p className="text-gray-300 text-sm">Heartbeat</p>
                    <div className="flex items-center gap-2">
                        <span className="w-3 h-3 rounded-full bg-green-500 animate-pulse"></span>
                        <span className="text-green-400 font-medium text-sm">OK</span>
                    </div>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
                    <p className="text-gray-300 text-sm">Queue Delay</p>
                    <span className="text-white font-medium text-sm">1.2s</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
                    <p className="text-gray-300 text-sm">Running Jobs</p>
                    <span className="text-white font-medium text-sm">48</span>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5">
                    <p className="text-gray-300 text-sm">Idle Workers</p>
                    <span className="text-white font-medium text-sm">2</span>
                </div>
            </div>
        </div>
    );
};

export default WorkerHealthCard;
