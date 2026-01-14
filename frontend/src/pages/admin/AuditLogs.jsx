import { useState, useEffect } from 'react';
import { FileText, Filter, ChevronLeft, ChevronRight, Search, RefreshCw, Activity, Clock, Shield } from 'lucide-react';
import api from '../../api/axios';

const EVENT_TYPE_LABELS = {
    'scan.completed': { label: 'Scan Completed', color: 'bg-green-500/10 text-green-400 border-green-500/20' },
    'scan.failed': { label: 'Scan Failed', color: 'bg-red-500/10 text-red-400 border-red-500/20' },
    'scan.started': { label: 'Scan Started', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
    'user.login': { label: 'User Login', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
    'user.logout': { label: 'User Logout', color: 'bg-gray-500/10 text-gray-400 border-gray-500/20' },
    'user.created': { label: 'User Created', color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
    'repo.added': { label: 'Repo Added', color: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' },
    'repo.deleted': { label: 'Repo Deleted', color: 'bg-orange-500/10 text-orange-400 border-orange-500/20' },
    'member.invited': { label: 'Member Invited', color: 'bg-pink-500/10 text-pink-400 border-pink-500/20' },
    'webhook.received': { label: 'Webhook', color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
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
        <>
            {/* Title Section */}
            <div className="flex flex-col sm:flex-row justify-between gap-4 items-start sm:items-center">
                <div className="flex items-center gap-4">
                    <div className="flex flex-col gap-1">
                        <h1 className="text-white text-2xl sm:text-3xl font-black leading-tight tracking-tight">Audit Logs</h1>
                        <p className="text-gray-400 text-sm sm:text-base font-normal leading-normal">System-wide activity and security audit trail</p>
                    </div>
                </div>
                <button
                    onClick={() => { fetchLogs(); fetchStats(); }}
                    className="btn btn-primary h-10 sm:h-11 px-4 sm:px-6 rounded-lg text-sm font-medium gap-2 hover:shadow-lg hover:shadow-primary/20 border-none w-full sm:w-auto"
                >
                    <RefreshCw className="w-5 h-5" />
                    Refresh
                </button>
            </div>

            {/* Stats Grid */}
            {stats && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="flex flex-col gap-2 rounded-xl border border-white/10 bg-[#0A0F16] p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 rounded-lg bg-primary/10 text-primary">
                                <Activity className="w-5 h-5" />
                            </div>
                            <p className="text-gray-400 text-base font-medium leading-normal">Total Events</p>
                        </div>
                        <p className="text-white tracking-tight text-3xl font-bold leading-tight">{stats.total}</p>
                    </div>
                    <div className="flex flex-col gap-2 rounded-xl border border-white/10 bg-[#0A0F16] p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 rounded-lg bg-green-500/10 text-green-500">
                                <Clock className="w-5 h-5" />
                            </div>
                            <p className="text-gray-400 text-base font-medium leading-normal">Last 24 Hours</p>
                        </div>
                        <p className="text-white tracking-tight text-3xl font-bold leading-tight">{stats.last_24h}</p>
                    </div>
                    <div className="flex flex-col gap-2 rounded-xl border border-white/10 bg-[#0A0F16] p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500">
                                <Shield className="w-5 h-5" />
                            </div>
                            <p className="text-gray-400 text-base font-medium leading-normal">Last 7 Days</p>
                        </div>
                        <p className="text-white tracking-tight text-3xl font-bold leading-tight">{stats.last_7d}</p>
                    </div>
                    <div className="flex flex-col gap-2 rounded-xl border border-white/10 bg-[#0A0F16] p-6">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-500">
                                <FileText className="w-5 h-5" />
                            </div>
                            <p className="text-gray-400 text-base font-medium leading-normal">Event Types</p>
                        </div>
                        <p className="text-white tracking-tight text-3xl font-bold leading-tight">{stats.by_type?.length || 0}</p>
                    </div>
                </div>
            )}

            {/* Audit Logs Table */}
            <div className="rounded-xl border border-white/10 bg-[#0A0F16]">
                {/* Toolbar */}
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 p-4">
                    <div className="relative w-full max-w-xs">
                        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                            <Search className="w-5 h-5 text-gray-400" />
                        </div>
                        <input
                            className="block w-full rounded-lg border-white/10 bg-white/5 pl-10 text-sm text-white placeholder-gray-400 focus:border-primary focus:ring-primary"
                            placeholder="Search by email..."
                            type="text"
                            value={searchEmail}
                            onChange={(e) => setSearchEmail(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch(e)}
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <select
                            className="rounded-lg border-white/10 bg-white/5 text-sm text-white focus:border-primary focus:ring-primary"
                            value={filter}
                            onChange={(e) => { setFilter(e.target.value); setPage(1); }}
                        >
                            <option value="">All Events</option>
                            {Object.entries(EVENT_TYPE_LABELS).map(([key, val]) => (
                                <option key={key} value={key}>{val.label}</option>
                            ))}
                        </select>
                        <button
                            onClick={handleSearch}
                            className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white transition-colors"
                        >
                            <Filter className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-white/5 border-b border-white/10">
                            <tr>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Event</th>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Actor</th>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Target</th>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Tenant</th>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">IP Address</th>
                                <th className="px-6 py-3 text-xs font-medium uppercase tracking-wider text-gray-400">Time</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {loading ? (
                                <tr>
                                    <td colSpan="6" className="py-8 text-center text-gray-500">Loading audit logs...</td>
                                </tr>
                            ) : logs.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="py-8 text-center text-gray-500">No audit logs found.</td>
                                </tr>
                            ) : (
                                logs.map((log) => {
                                    const eventInfo = EVENT_TYPE_LABELS[log.event_type] || { label: log.event_type, color: 'bg-gray-500/10 text-gray-400 border-gray-500/20' };
                                    return (
                                        <tr key={log.id} className="hover:bg-white/5 transition-colors">
                                            <td className="whitespace-nowrap px-6 py-4">
                                                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border ${eventInfo.color}`}>
                                                    {eventInfo.label}
                                                </span>
                                            </td>
                                            <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-400">{log.actor_email || '-'}</td>
                                            <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-400">
                                                {log.target_name || log.target_type || '-'}
                                            </td>
                                            <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-400">{log.tenant_name || '-'}</td>
                                            <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 font-mono">{log.ip_address || '-'}</td>
                                            <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-400">{formatDate(log.created_at)}</td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between border-t border-white/10 px-4 py-3 sm:px-6">
                        <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                            <div>
                                <p className="text-sm text-gray-400">
                                    Page <span className="font-medium text-white">{page}</span> of <span className="font-medium text-white">{totalPages}</span>
                                </p>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <ChevronLeft className="w-5 h-5" />
                                </button>
                                <button
                                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                    disabled={page === totalPages}
                                    className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <ChevronRight className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
};

export default AuditLogs;
