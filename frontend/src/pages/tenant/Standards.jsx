import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Shield, Plus, Edit2, Trash2, ChevronRight, Search, BookOpen, Building2 } from 'lucide-react';
import { toast } from 'react-toastify';
import { getStandards, getStandardRules, createStandard, updateStandard, deleteStandard } from '../../api/services/standards';
import { showConfirmDialog, showSuccessToast, showErrorToast } from '../../utils/sweetAlert';

const Standards = () => {
    const { tenant } = useAuth();
    const [standards, setStandards] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showRulesModal, setShowRulesModal] = useState(false);
    const [selectedStandard, setSelectedStandard] = useState(null);
    const [standardRules, setStandardRules] = useState([]);
    const [loadingRules, setLoadingRules] = useState(false);
    const [formData, setFormData] = useState({ name: '', description: '' });
    const [isEditing, setIsEditing] = useState(false);

    useEffect(() => {
        if (tenant) {
            fetchStandards();
        }
    }, [tenant]);

    const fetchStandards = async () => {
        setLoading(true);
        try {
            const data = await getStandards(tenant.id);
            // API returns either { standards: [...] } or direct array
            setStandards(data.standards || (Array.isArray(data) ? data : []));
        } catch (error) {
            toast.error('Failed to load standards');
        } finally {
            setLoading(false);
        }
    };

    const handleViewRules = async (standard) => {
        setSelectedStandard(standard);
        setShowRulesModal(true);
        setLoadingRules(true);
        try {
            const data = await getStandardRules(standard.slug);
            // API returns either { rules: [...] } or direct array
            setStandardRules(data.rules || (Array.isArray(data) ? data : []));
        } catch (error) {
            toast.error('Failed to load rules');
            setStandardRules([]);
        } finally {
            setLoadingRules(false);
        }
    };

    const handleEdit = (standard) => {
        setSelectedStandard(standard);
        setFormData({ name: standard.name, description: standard.description || '' });
        setIsEditing(true);
        setShowCreateModal(true);
    };

    const handleCreate = () => {
        setSelectedStandard(null);
        setFormData({ name: '', description: '' });
        setIsEditing(false);
        setShowCreateModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!formData.name.trim()) {
            toast.error('Name is required');
            return;
        }

        try {
            if (isEditing && selectedStandard) {
                await updateStandard(selectedStandard.slug, formData);
                showSuccessToast('Standard updated successfully');
            } else {
                await createStandard(tenant.id, formData);
                showSuccessToast('Standard created successfully');
            }
            setShowCreateModal(false);
            fetchStandards();
        } catch (error) {
            showErrorToast(isEditing ? 'Failed to update standard' : 'Failed to create standard');
        }
    };

    const handleDelete = async (standard) => {
        if (standard.is_builtin) {
            toast.error('Built-in standards cannot be deleted');
            return;
        }

        const confirmed = await showConfirmDialog({
            title: 'Delete Standard?',
            text: `This will permanently delete "${standard.name}" and all its rules. This action cannot be undone.`,
            icon: 'warning'
        });

        if (confirmed) {
            try {
                await deleteStandard(standard.slug);
                showSuccessToast('Standard deleted successfully');
                fetchStandards();
            } catch (error) {
                showErrorToast('Failed to delete standard');
            }
        }
    };

    const filteredStandards = standards.filter(s =>
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (s.description && s.description.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const builtInStandards = filteredStandards.filter(s => s.is_builtin);
    const customStandards = filteredStandards.filter(s => !s.is_builtin);

    const StandardCard = ({ standard }) => (
        <div className="bg-[#0F1419] border border-white/10 rounded-xl p-5 hover:border-primary/50 transition-all">
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${standard.is_builtin ? 'bg-blue-500/20' : 'bg-primary/20'}`}>
                        {standard.is_builtin ? (
                            <BookOpen className="w-5 h-5 text-blue-400" />
                        ) : (
                            <Building2 className="w-5 h-5 text-primary" />
                        )}
                    </div>
                    <div>
                        <h3 className="text-white font-medium">{standard.name}</h3>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${standard.is_builtin ? 'bg-blue-500/20 text-blue-400' : 'bg-primary/20 text-primary'}`}>
                            {standard.is_builtin ? 'Built-in' : 'Custom'}
                        </span>
                    </div>
                </div>
                {!standard.is_builtin && (
                    <div className="flex gap-2">
                        <button
                            onClick={() => handleEdit(standard)}
                            className="p-1.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                        >
                            <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => handleDelete(standard)}
                            className="p-1.5 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                )}
            </div>
            <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                {standard.description || 'No description provided'}
            </p>
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-sm text-gray-400">
                    <span>{standard.rule_count || 0} rules</span>
                    <span>Weight: {standard.total_weight || 0}</span>
                </div>
                <button
                    onClick={() => handleViewRules(standard)}
                    className="flex items-center gap-1 text-primary hover:text-primary/80 text-sm font-medium transition-colors"
                >
                    View Rules <ChevronRight className="w-4 h-4" />
                </button>
            </div>
        </div>
    );

    return (
        <div className="p-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Shield className="w-7 h-7 text-primary" />
                        Standards Management
                    </h1>
                    <p className="text-gray-400 mt-1">Manage compliance standards and rules for your repositories</p>
                </div>
                <button
                    onClick={handleCreate}
                    className="flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors"
                >
                    <Plus className="w-5 h-5" />
                    Create Standard
                </button>
            </div>

            {/* Search */}
            <div className="relative mb-6">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                    type="text"
                    placeholder="Search standards..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full md:w-80 pl-10 pr-4 py-2 bg-[#0F1419] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none"
                />
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
                </div>
            ) : (
                <>
                    {/* Built-in Standards */}
                    {builtInStandards.length > 0 && (
                        <div className="mb-8">
                            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                <BookOpen className="w-5 h-5 text-blue-400" />
                                Built-in Standards
                            </h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {builtInStandards.map(standard => (
                                    <StandardCard key={standard.id} standard={standard} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Custom Standards */}
                    <div>
                        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <Building2 className="w-5 h-5 text-primary" />
                            Custom Standards
                        </h2>
                        {customStandards.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {customStandards.map(standard => (
                                    <StandardCard key={standard.id} standard={standard} />
                                ))}
                            </div>
                        ) : (
                            <div className="bg-[#0F1419] border border-white/10 rounded-xl p-10 text-center">
                                <Shield className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                                <h3 className="text-white font-medium mb-2">No custom standards yet</h3>
                                <p className="text-gray-400 text-sm mb-4">Create your first custom compliance standard to get started</p>
                                <button
                                    onClick={handleCreate}
                                    className="inline-flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors"
                                >
                                    <Plus className="w-5 h-5" />
                                    Create Standard
                                </button>
                            </div>
                        )}
                    </div>
                </>
            )}

            {/* Create/Edit Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="bg-[#0A0F16] border border-white/10 rounded-xl w-full max-w-md p-6 mx-4">
                        <h2 className="text-xl font-bold text-white mb-4">
                            {isEditing ? 'Edit Standard' : 'Create New Standard'}
                        </h2>
                        <form onSubmit={handleSubmit}>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full px-3 py-2 bg-[#0F1419] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none"
                                    placeholder="e.g., Internal Security Policy"
                                    required
                                />
                            </div>
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    className="w-full px-3 py-2 bg-[#0F1419] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none resize-none"
                                    rows={3}
                                    placeholder="Describe the purpose of this standard..."
                                />
                            </div>
                            <div className="flex gap-3 justify-end">
                                <button
                                    type="button"
                                    onClick={() => setShowCreateModal(false)}
                                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors"
                                >
                                    {isEditing ? 'Save Changes' : 'Create Standard'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Rules Modal */}
            {showRulesModal && selectedStandard && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="bg-[#0A0F16] border border-white/10 rounded-xl w-full max-w-2xl max-h-[80vh] overflow-hidden mx-4">
                        <div className="p-6 border-b border-white/10">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h2 className="text-xl font-bold text-white">{selectedStandard.name}</h2>
                                    <p className="text-gray-400 text-sm mt-1">{selectedStandard.description}</p>
                                </div>
                                <button
                                    onClick={() => setShowRulesModal(false)}
                                    className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    ✕
                                </button>
                            </div>
                        </div>
                        <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
                            {loadingRules ? (
                                <div className="flex items-center justify-center py-10">
                                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
                                </div>
                            ) : standardRules.length > 0 ? (
                                <div className="space-y-3">
                                    {standardRules.map((rule, index) => (
                                        <div key={rule.id || index} className="bg-[#0F1419] border border-white/10 rounded-lg p-4">
                                            <div className="flex items-start justify-between mb-2">
                                                <h4 className="text-white font-medium">{rule.name}</h4>
                                                <div className="flex items-center gap-2">
                                                    <span className={`text-xs px-2 py-0.5 rounded-full ${rule.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                                                        rule.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                                                            rule.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                                                'bg-blue-500/20 text-blue-400'
                                                        }`}>
                                                        {rule.severity}
                                                    </span>
                                                    <span className="text-xs text-gray-400">Weight: {rule.weight}</span>
                                                </div>
                                            </div>
                                            <p className="text-gray-400 text-sm">{rule.description}</p>
                                            {rule.remediation_hint && (
                                                <p className="text-primary/70 text-xs mt-2">💡 {rule.remediation_hint}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-10">
                                    <Shield className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                                    <p className="text-gray-400">No rules defined for this standard</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Standards;
