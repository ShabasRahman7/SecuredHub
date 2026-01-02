import { useLocation, Link } from 'react-router-dom';
import { Construction, ArrowLeft } from 'lucide-react';

const AdminPlaceholder = () => {
    const location = useLocation();

    // extract feature name from path (e.g., "/admin/ai" -> "AI Management")
    const getFeatureName = (pathname) => {
        const path = pathname.split('/').pop();
        const map = {
            'workers': 'Worker Monitoring',
            'ai': 'AI Management',
            'audit-logs': 'Audit System',
            'settings': 'Platform Settings'
        };
        return map[path] || 'Feature';
    };

    const featureName = getFeatureName(location.pathname);

    return (
        <>
            {/* Title Section */}
            <div className="flex flex-col gap-1 mb-6">
                <h1 className="text-white text-2xl sm:text-3xl font-black leading-tight tracking-tight">{featureName}</h1>
            </div>

            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-8">
            <div className="bg-gray-800 p-6 rounded-full mb-6 relative overflow-hidden group">
                <div className="absolute inset-0 bg-blue-500/20 blur-xl group-hover:bg-blue-500/30 transition-all duration-500"></div>
                <Construction className="w-16 h-16 text-blue-400 relative z-10" />
            </div>

            <h2 className="text-3xl font-bold text-white mb-3 tracking-tight">
                {featureName}
            </h2>
            <p className="text-gray-400 max-w-md mb-8 text-lg">
                This administrative module is currently under active development. Check back soon for updates.
            </p>

            <Link
                to="/admin/dashboard"
                className="btn btn-primary bg-blue-600 hover:bg-blue-700 border-none text-white gap-2 px-8"
            >
                <ArrowLeft className="w-4 h-4" />
                Return to Dashboard
            </Link>
            </div>
        </>
    );
};

export default AdminPlaceholder;
