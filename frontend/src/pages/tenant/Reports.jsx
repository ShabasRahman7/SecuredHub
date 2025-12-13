import { Link as LinkIcon } from 'lucide-react';

const Reports = () => {
    return (
        <>
            {/* Title Section */}
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">Reports</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        View security reports and analytics.
                    </p>
                </div>
            </div>

            {/* Placeholder Content */}
            <div className="flex flex-col items-center justify-center h-96 bg-white dark:bg-[#1a1d21] border border-[#e5e7eb] dark:border-[#282f39] rounded-xl text-center p-8">
                <div className="bg-gray-100 dark:bg-white/5 p-4 rounded-full mb-4">
                    <LinkIcon className="w-12 h-12 text-gray-400" />
                </div>
                <h3 className="text-xl font-bold mb-2">Reports Module</h3>
                <p className="text-gray-500 max-w-md">
                    This feature is currently under development. Please check back later for updates on reports functionality.
                </p>
            </div>
        </>
    );
};

export default Reports;

