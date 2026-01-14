import { useState, useEffect } from 'react';
import { FileText, Filter, ChevronLeft, ChevronRight, Search, RefreshCw } from 'lucide-react';
import api from '../../api/axios';

const EVENT_TYPE_LABELS = {
    'scan.completed': { label: 'Scan Completed', color: 'bg-green-500/20 text-green-400' },
    'scan.failed': { label: 'Scan Failed', color: 'bg-red-500/20 text-red-400' },
    'scan.started': { label: 'Scan Started', color: 'bg-blue-500/20 text-blue-400' },
    'user.login': { label: 'User Login', color: 'bg-purple-500/20 text-purple-400' },
    'user.logout': { label: 'User Logout', color: 'bg-gray-500/20 text-gray-400' },
    'user.created': { label: 'User Created', color: 'bg-cyan-500/20 text-cyan-400' },
    'repo.added': { label: 'Repo Added', color: 'bg-yellow-500/20 text-yellow-400' },
    'repo.deleted': { label: 'Repo Deleted', color: 'bg-orange-500/20 text-orange-400' },
    'member.invited': { label: 'Member Invited', color: 'bg-pink-500/20 text-pink-400' },
    'webhook.received': { label: 'Webhook', color: 'bg-indigo-500/20 text-indigo-400' },
};

const AuditLogs = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState(null);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [filter, setFilter] = useState('');
    const [searchEmail, setSearchEmail] = useState('');

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({ page });
            if (filter) params.append('event_type', filter);
            if (searchEmail) params.append('actor_email', searchEmail);

            const response = await api.get(`/admin/audit-logs/?${params}`);
            setLogs(response.data.results);
            setTotalPages(Math.ceil(response.data.count / 25));
        } catch (error) {
            console.error('Failed to fetch audit logs:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const response = await api.get('/admin/audit-logs/stats/');
            setStats(response.data);
        } catch (error) {
            console.error('Failed to fetch audit stats:', error);
        }
    };

    useEffect(() => {
        fetchLogs();
        fetchStats();
    }, [page, filter]);

    const handleSearch = (e) => {
        e.preventDefault();
        setPage(1);
        fetchLogs();
    };

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleString();
    };

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Audit Logs</h1>
                    <p className="text-gray-400 mt-1">System-wide activity and security audit trail</p>
                </div>
                <button
                    onClick={() => { fetchLogs(); fetchStats(); }}
                    className="flex items-center gap-2 px-4 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors"
                >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                </button>
            </div>

            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-[#111827] rounded-xl p-4 border border-white/10">
                        <p className="text-gray-400 text-sm">Total Events</p>
                        <p className="text-2xl font-bold text-white">{stats.total}</p>
                    </div>
                    <div className="bg-[#111827] rounded-xl p-4 border border-white/10">
                        <p className="text-gray-400 text-sm">Last 24 Hours</p>
                        <p className="text-2xl font-bold text-primary">{stats.last_24h}</p>
                    </div>
                    <div className="bg-[#111827] rounded-xl p-4 border border-white/10">
                        <p className="text-gray-400 text-sm">Last 7 Days</p>
                        <p className="text-2xl font-bold text-white">{stats.last_7d}</p>
                    </div>
                    <div className="bg-[#111827] rounded-xl p-4 border border-white/10">
                        <p className="text-gray-400 text-sm">Event Types</p>
                        <p className="text-2xl font-bold text-white">{stats.by_type?.length || 0}</p>
                    </div>
                </div>
            )}

            <div className="bg-[#111827] rounded-xl border border-white/10">
                <div className="p-4 border-b border-white/10 flex flex-wrap gap-4 items-center">
                    <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-gray-400" />
                        <select
                            value={filter}
                            onChange={(e) => { setFilter(e.target.value); setPage(1); }}
                            className="bg-[#0A0F16] border border-white/10 rounded-lg px-3 py-2 text-white text-sm"
                        >
                            <option value="">All Events</option>
                            {Object.entries(EVENT_TYPE_LABELS).map(([key, val]) => (
                                <option key={key} value={key}>{val.label}</option>
                            ))}
                        </select>
                    </div>

                    <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1 max-w-md">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search by email..."
                                value={searchEmail}
                                onChange={(e) => setSearchEmail(e.target.value)}
                                className="w-full bg-[#0A0F16] border border-white/10 rounded-lg pl-10 pr-4 py-2 text-white text-sm"
                            />
                        </div>
                        <button type="submit" className="px-4 py-2 bg-primary text-black rounded-lg text-sm font-medium">
                            Search
                        </button>
                    </form>
                </div>

                {loading ? (
                    <div className="p-8 text-center text-gray-400">Loading...</div>
                ) : logs.length === 0 ? (
                    <div className="p-8 text-center text-gray-400">No audit logs found</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-white/10">
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Event</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Actor</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Target</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Tenant</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">IP</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Time</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {logs.map((log) => {
                                    const eventInfo = EVENT_TYPE_LABELS[log.event_type] || { label: log.event_type, color: 'bg-gray-500/20 text-gray-400' };
                                    return (
                                        <tr key={log.id} className="hover:bg-white/5">
                                            <td className="px-4 py-3">
                                                <span className={`px-2 py-1 rounded text-xs font-medium ${eventInfo.color}`}>
                                                    {eventInfo.label}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-sm text-gray-300">{log.actor_email || '-'}</td>
                                            <td className="px-4 py-3 text-sm text-gray-300">
                                                {log.target_name || log.target_type || '-'}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-gray-300">{log.tenant_name || '-'}</td>
                                            <td className="px-4 py-3 text-sm text-gray-500 font-mono">{log.ip_address || '-'}</td>
                                            <td className="px-4 py-3 text-sm text-gray-400">{formatDate(log.created_at)}</td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}

                {totalPages > 1 && (
                    <div className="p-4 border-t border-white/10 flex items-center justify-between">
                        <p className="text-sm text-gray-400">Page {page} of {totalPages}</p>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="p-2 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10 disabled:opacity-50"
                            >
                                <ChevronLeft className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="p-2 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10 disabled:opacity-50"
                            >
                                <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AuditLogs;
