import { Bot } from 'lucide-react';

const AIAssistant = () => {
    return (
        <>
            {/* Title Section */}
            <div className="flex flex-wrap justify-between items-center gap-4">
                <div className="flex min-w-72 flex-col gap-1">
                    <p className="text-2xl lg:text-3xl font-bold leading-tight tracking-tight">AI Assistant</p>
                    <p className="text-[#6b7280] dark:text-[#9da8b9] text-sm lg:text-base font-normal">
                        Get AI-powered help with security vulnerabilities.
                    </p>
                </div>
            </div>

            {/* Placeholder Content */}
            <div className="flex flex-col items-center justify-center h-96 bg-[#0A0F16] border border-white/10 rounded-xl text-center p-8">
                <div className="bg-white/5 p-4 rounded-full mb-4">
                    <Bot className="w-12 h-12 text-gray-400" />
                </div>
                <h3 className="text-xl font-bold mb-2 text-white">AI Assistant</h3>
                <p className="text-gray-500">This module is coming soon in Week 2.</p>
            </div>
        </>
    );
};

export default AIAssistant;


