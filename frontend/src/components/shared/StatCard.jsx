import { ArrowUp, ArrowDown } from 'lucide-react';

const StatCard = ({ title, value, trend, trendValue, trendDirection = 'up', subtext }) => {
    const isPositive = trendDirection === 'up';
    const TrendIcon = isPositive ? ArrowUp : ArrowDown;
    const trendColor = isPositive ? 'text-green-500' : 'text-red-500';

    return (
        <div className="flex flex-1 flex-col gap-2 rounded-xl p-6 bg-[#0A0F16] border border-white/10 shadow-lg">
            <p className="text-gray-400 text-sm font-medium leading-normal">{title}</p>
            <p className="text-white tracking-tight text-3xl font-bold leading-tight">{value}</p>
            {trend ? (
                <p className={`${trendColor} text-sm font-medium leading-normal flex items-center gap-1`}>
                    <TrendIcon className="w-4 h-4" />
                    {trendValue}
                </p>
            ) : (
                <p className="text-gray-500 text-sm font-medium leading-normal">{subtext}</p>
            )}
        </div>
    );
};

export default StatCard;
