import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { BookOpen, ChevronDown, ChevronRight, Edit2, ToggleLeft, ToggleRight, Save, X, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../../api/axios';

/**
 * AdminStandards - Platform admin page for managing built-in compliance standards.
 * 
 * Features:
 * - View all built-in standards with their rules
 * - Toggle standards active/inactive (affects tenant visibility)
 * - Edit standard metadata (name, description, version)
 * - Edit rule properties (weight, severity, description)
 * - Toggle individual rules active/inactive
 */
const AdminStandards = () => {
    const { user } = useAuth();
    const [standards, setStandards] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [expandedStandard, setExpandedStandard] = useState(null);

    // Edit modals
    const [editingStandard, setEditingStandard] = useState(null);
    const [editingRule, setEditingRule] = useState(null);
    const [editForm, setEditForm] = useState({});
    const [saving, setSaving] = useState(false);

    // Fetch all built-in standards
    const fetchStandards = async () => {
        try {
            setLoading(true);
            const response = await api.get('/standards/admin/');
            setStandards(response.data);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch standards:', err);
            setError('Failed to load standards. Make sure you have admin access.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStandards();
    }, []);

    // Toggle standard active/inactive
    const handleToggleStandard = async (standard) => {
        try {
            const response = await api.post(`/standards/admin/${standard.slug}/toggle/`);
            toast.success(response.data.message);
            fetchStandards();
        } catch (err) {
            toast.error('Failed to toggle standard');
        }
    };

    // Toggle rule active/inactive
    const handleToggleRule = async (standardSlug, rule) => {
        try {
            const response = await api.post(`/standards/admin/${standardSlug}/rules/${rule.id}/toggle/`);
            toast.success(response.data.message);
            fetchStandards();
        } catch (err) {
            toast.error('Failed to toggle rule');
        }
    };

    // Open edit standard modal
    const handleEditStandard = (standard) => {
        setEditingStandard(standard);
        setEditForm({
            name: standard.name,
            description: standard.description,
            version: standard.version,
        });
    };

    // Open edit rule modal
    const handleEditRule = (standardSlug, rule) => {
        setEditingRule({ ...rule, standardSlug });
        setEditForm({
            description: rule.description,
            weight: rule.weight,
            severity: rule.severity,
            remediation_hint: rule.remediation_hint,
        });
    };

    // Save standard changes
    const handleSaveStandard = async () => {
        if (!editingStandard) return;

        try {
            setSaving(true);
            await api.patch(`/standards/admin/${editingStandard.slug}/update/`, editForm);
            toast.success('Standard updated successfully');
            setEditingStandard(null);
            fetchStandards();
        } catch (err) {
            toast.error('Failed to update standard');
        } finally {
            setSaving(false);
        }
    };

    // Save rule changes
    const handleSaveRule = async () => {
        if (!editingRule) return;

        try {
            setSaving(true);
            await api.patch(`/standards/admin/${editingRule.standardSlug}/rules/${editingRule.id}/update/`, editForm);
            toast.success('Rule updated successfully');
            setEditingRule(null);
            fetchStandards();
        } catch (err) {
            toast.error('Failed to update rule');
        } finally {
            setSaving(false);
        }
    };

    // Get severity badge color
    const getSeverityColor = (severity) => {
        switch (severity) {
            case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/50';
            case 'high': return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
            case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
            case 'low': return 'bg-green-500/20 text-green-400 border-green-500/50';
            default: return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
        }
    };

    // Standard card component
    const StandardCard = ({ standard }) => {
        const isExpanded = expandedStandard === standard.slug;
        const activeRules = standard.rules?.filter(r => r.is_active).length || 0;
        const totalRules = standard.rules?.length || 0;

        return (
            <div className={`bg-[#0D1117] border rounded-xl overflow-hidden transition-all ${standard.is_active ? 'border-white/10' : 'border-red-500/30 opacity-75'
                }`}>
                {/* Header */}
                <div className="p-6">
                    <div className="flex items-start justify-between">
                        <div className="flex items-start gap-4 flex-1">
                            <div className={`p-3 rounded-lg ${standard.is_active ? 'bg-primary/20' : 'bg-red-500/20'}`}>
                                <BookOpen className={`w-6 h-6 ${standard.is_active ? 'text-primary' : 'text-red-400'}`} />
                            </div>
                            <div className="flex-1">
                                <div className="flex items-center gap-3">
                                    <h3 className="text-lg font-semibold text-white">{standard.name}</h3>
                                    <span className="text-xs px-2 py-0.5 rounded bg-white/10 text-gray-400">
                                        v{standard.version}
                                    </span>
                                    {!standard.is_active && (
                                        <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400">
                                            Inactive
                                        </span>
                                    )}
                                </div>
                                <p className="text-gray-400 text-sm mt-1 line-clamp-2">{standard.description}</p>
                                <div className="flex items-center gap-4 mt-3">
                                    <span className="text-sm text-gray-500">
                                        <strong className="text-white">{activeRules}</strong>/{totalRules} rules active
                                    </span>
                                    <span className="text-sm text-gray-500">
                                        Total Weight: <strong className="text-white">{standard.total_weight || 0}</strong>
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => handleEditStandard(standard)}
                                className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                                title="Edit Standard"
                            >
                                <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => handleToggleStandard(standard)}
                                className={`p-2 rounded-lg transition-colors ${standard.is_active
                                        ? 'text-green-400 hover:bg-green-500/20'
                                        : 'text-red-400 hover:bg-red-500/20'
                                    }`}
                                title={standard.is_active ? 'Deactivate' : 'Activate'}
                            >
                                {standard.is_active ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
                            </button>
                            <button
                                onClick={() => setExpandedStandard(isExpanded ? null : standard.slug)}
                                className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                            >
                                {isExpanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Expanded Rules */}
                {isExpanded && (
                    <div className="border-t border-white/10 bg-[#080B10]">
                        <div className="p-4">
                            <h4 className="text-sm font-medium text-gray-400 mb-3">Rules ({totalRules})</h4>
                            <div className="space-y-2">
                                {standard.rules?.map((rule) => (
                                    <div
                                        key={rule.id}
                                        className={`flex items-center justify-between p-3 rounded-lg border transition-all ${rule.is_active
                                                ? 'bg-[#0D1117] border-white/10'
                                                : 'bg-red-500/5 border-red-500/20 opacity-60'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3 flex-1">
                                            {rule.is_active ? (
                                                <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                                            ) : (
                                                <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                                            )}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-white text-sm font-medium truncate">{rule.name}</span>
                                                    <span className={`text-xs px-2 py-0.5 rounded border ${getSeverityColor(rule.severity)}`}>
                                                        {rule.severity}
                                                    </span>
                                                </div>
                                                <p className="text-gray-500 text-xs mt-0.5 truncate">{rule.description}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <div className="text-right">
                                                <span className="text-xs text-gray-500">Weight</span>
                                                <p className="text-white font-semibold">{rule.weight}</p>
                                            </div>
                                            <button
                                                onClick={() => handleEditRule(standard.slug, rule)}
                                                className="p-1.5 text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors"
                                            >
                                                <Edit2 className="w-3.5 h-3.5" />
                                            </button>
                                            <button
                                                onClick={() => handleToggleRule(standard.slug, rule)}
                                                className={`p-1.5 rounded transition-colors ${rule.is_active
                                                        ? 'text-green-400 hover:bg-green-500/20'
                                                        : 'text-red-400 hover:bg-red-500/20'
                                                    }`}
                                            >
                                                {rule.is_active ? <ToggleRight className="w-4 h-4" /> : <ToggleLeft className="w-4 h-4" />}
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    // Edit Standard Modal
    const EditStandardModal = () => {
        if (!editingStandard) return null;

        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
                <div className="bg-[#0D1117] border border-white/10 rounded-xl w-full max-w-lg mx-4">
                    <div className="flex items-center justify-between p-4 border-b border-white/10">
                        <h3 className="text-lg font-semibold text-white">Edit Standard</h3>
                        <button onClick={() => setEditingStandard(null)} className="text-gray-400 hover:text-white">
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                    <div className="p-4 space-y-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Name</label>
                            <input
                                type="text"
                                value={editForm.name || ''}
                                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                                className="w-full px-3 py-2 bg-[#080B10] border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Version</label>
                            <input
                                type="text"
                                value={editForm.version || ''}
                                onChange={(e) => setEditForm({ ...editForm, version: e.target.value })}
                                className="w-full px-3 py-2 bg-[#080B10] border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Description</label>
                            <textarea
                                value={editForm.description || ''}
                                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                                rows={4}
                                className="w-full px-3 py-2 bg-[#080B10] border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-none"
                            />
                        </div>
                    </div>
                    <div className="flex justify-end gap-3 p-4 border-t border-white/10">
                        <button
                            onClick={() => setEditingStandard(null)}
                            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSaveStandard}
                            disabled={saving}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                        >
                            <Save className="w-4 h-4" />
                            {saving ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </div>
            </div>
        );
    };

    // Edit Rule Modal
    const EditRuleModal = () => {
        if (!editingRule) return null;

        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
                <div className="bg-[#0D1117] border border-white/10 rounded-xl w-full max-w-lg mx-4">
                    <div className="flex items-center justify-between p-4 border-b border-white/10">
                        <h3 className="text-lg font-semibold text-white">Edit Rule</h3>
                        <button onClick={() => setEditingRule(null)} className="text-gray-400 hover:text-white">
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                    <div className="p-4 space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Weight (1-10)</label>
                                <input
                                    type="number"
                                    min="1"
                                    max="10"
                                    value={editForm.weight || 5}
                                    onChange={(e) => setEditForm({ ...editForm, weight: parseInt(e.target.value) })}
                                    className="w-full px-3 py-2 bg-[#080B10] border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-400 mb-1">Severity</label>
                                <select
                                    value={editForm.severity || 'medium'}
                                    onChange={(e) => setEditForm({ ...editForm, severity: e.target.value })}
                                    className="w-full px-3 py-2 bg-[#080B10] border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                                >
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                    <option value="critical">Critical</option>
                                </select>
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Description</label>
                            <textarea
                                value={editForm.description || ''}
                                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                                rows={3}
                                className="w-full px-3 py-2 bg-[#080B10] border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-none"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Remediation Hint</label>
                            <textarea
                                value={editForm.remediation_hint || ''}
                                onChange={(e) => setEditForm({ ...editForm, remediation_hint: e.target.value })}
                                rows={3}
                                className="w-full px-3 py-2 bg-[#080B10] border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-primary focus:border-transparent outline-none resize-none"
                            />
                        </div>
                    </div>
                    <div className="flex justify-end gap-3 p-4 border-t border-white/10">
                        <button
                            onClick={() => setEditingRule(null)}
                            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSaveRule}
                            disabled={saving}
                            className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
                        >
                            <Save className="w-4 h-4" />
                            {saving ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </div>
            </div>
        );
    };

    // Loading state
    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-center">
                <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
                <p className="text-red-400">{error}</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Compliance Standards</h1>
                    <p className="text-gray-400 mt-1">Manage platform-wide built-in compliance standards</p>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                    <span className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-green-400"></div>
                        {standards.filter(s => s.is_active).length} Active
                    </span>
                    <span className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-red-400"></div>
                        {standards.filter(s => !s.is_active).length} Inactive
                    </span>
                </div>
            </div>

            {/* Standards List */}
            <div className="space-y-4">
                {standards.length === 0 ? (
                    <div className="text-center py-12 text-gray-400">
                        <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>No built-in standards found.</p>
                        <p className="text-sm">Load standards using the management command.</p>
                    </div>
                ) : (
                    standards.map((standard) => (
                        <StandardCard key={standard.slug} standard={standard} />
                    ))
                )}
            </div>

            {/* Modals */}
            <EditStandardModal />
            <EditRuleModal />
        </div>
    );
};

export default AdminStandards;
