import { Link } from 'react-router-dom';

const TableCard = ({ title, subtitle, actionText, actionLink, children }) => {
    return (
        <div className="bg-[#0A0F16] border border-white/10 rounded-xl shadow-lg flex flex-col">
            <div className="p-6 flex justify-between items-center border-b border-white/10">
                <div>
                    <h3 className="text-white text-lg font-semibold">{title}</h3>
                    <p className="text-gray-400 text-sm">{subtitle}</p>
                </div>
                {actionText && actionLink && (
                    <Link to={actionLink} className="text-primary text-sm font-medium hover:underline">
                        {actionText}
                    </Link>
                )}
            </div>
            <div className="overflow-x-auto flex-1">
                {children}
            </div>
        </div>
    );
};

export default TableCard;
