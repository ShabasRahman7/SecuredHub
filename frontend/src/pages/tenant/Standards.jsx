import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Shield, Plus, Edit2, Trash2, ChevronRight, Search, BookOpen, Building2, X, AlertCircle } from 'lucide-react';
import { toast } from 'react-toastify';
import { getStandards, getStandardRules, createStandard, updateStandard, deleteStandard, addRule, updateRule, deleteRule } from '../../api/services/standards';
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

    // Rule management state
    const [showRuleModal, setShowRuleModal] = useState(false);
    const [editingRule, setEditingRule] = useState(null);
    const [ruleFormData, setRuleFormData] = useState({
        name: '',
        description: '',
        rule_type: 'file_exists',
        check_config: { path: '' },
        weight: 10,
        severity: 'medium',
        remediation_hint: '',
        order: 0
    });
    const [savingRule, setSavingRule] = useState(false);

    const RULE_TYPES = [
        { value: 'file_exists', label: 'Required File', configFields: ['path'] },
        { value: 'file_forbidden', label: 'Forbidden File', configFields: ['path', 'pattern'] },
        { value: 'folder_exists', label: 'Required Folder', configFields: ['path'] },
        { value: 'pattern_match', label: 'Pattern Match', configFields: ['pattern', 'should_exist'] },
        { value: 'config_check', label: 'Config Check', configFields: ['file', 'key', 'expected_value'] },
        { value: 'hygiene', label: 'Repo Hygiene', configFields: ['check_type'] }
    ];

    const SEVERITY_OPTIONS = ['low', 'medium', 'high', 'critical'];

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

    // Rule handlers
    const resetRuleForm = () => {
        setRuleFormData({
            name: '',
            description: '',
            rule_type: 'file_exists',
            check_config: { path: '' },
            weight: 10,
            severity: 'medium',
            remediation_hint: '',
            order: standardRules.length
        });
        setEditingRule(null);
    };

    const handleAddRule = () => {
        resetRuleForm();
        setShowRuleModal(true);
    };

    const handleEditRule = (rule) => {
        setRuleFormData({
            name: rule.name || '',
            description: rule.description || '',
            rule_type: rule.rule_type || 'file_exists',
            check_config: rule.check_config || { path: '' },
            weight: rule.weight || 10,
            severity: rule.severity || 'medium',
            remediation_hint: rule.remediation_hint || '',
            order: rule.order || 0
        });
        setEditingRule(rule);
        setShowRuleModal(true);
    };

    const handleDeleteRule = async (rule) => {
        const confirmed = await showConfirmDialog({
            title: 'Delete Rule?',
            text: `Delete "${rule.name}"? This cannot be undone.`,
            icon: 'warning'
        });

        if (confirmed && selectedStandard) {
            try {
                await deleteRule(selectedStandard.slug, rule.id);
                showSuccessToast('Rule deleted successfully');
                // Refresh rules
                const data = await getStandardRules(selectedStandard.slug);
                setStandardRules(data.rules || (Array.isArray(data) ? data : []));
                fetchStandards(); // Update rule count
            } catch (error) {
                showErrorToast('Failed to delete rule');
            }
        }
    };

    const handleRuleSubmit = async (e) => {
        e.preventDefault();
        if (!ruleFormData.name.trim()) {
            toast.error('Rule name is required');
            return;
        }
        if (!selectedStandard) return;

        setSavingRule(true);
        try {
            if (editingRule) {
                await updateRule(selectedStandard.slug, editingRule.id, ruleFormData);
                showSuccessToast('Rule updated successfully');
            } else {
                await addRule(selectedStandard.slug, ruleFormData);
                showSuccessToast('Rule added successfully');
            }
            setShowRuleModal(false);
            // Refresh rules
            const data = await getStandardRules(selectedStandard.slug);
            setStandardRules(data.rules || (Array.isArray(data) ? data : []));
            fetchStandards(); // Update rule count
        } catch (error) {
            showErrorToast(editingRule ? 'Failed to update rule' : 'Failed to add rule');
        } finally {
            setSavingRule(false);
        }
    };

    const updateCheckConfig = (key, value) => {
        setRuleFormData(prev => ({
            ...prev,
            check_config: { ...prev.check_config, [key]: value }
        }));
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
                                <div className="flex items-center gap-2">
                                    {!selectedStandard.is_builtin && (
                                        <button
                                            onClick={handleAddRule}
                                            className="flex items-center gap-1 px-3 py-1.5 bg-primary hover:bg-primary/90 text-white text-sm rounded-lg transition-colors"
                                        >
                                            <Plus className="w-4 h-4" />
                                            Add Rule
                                        </button>
                                    )}
                                    <button
                                        onClick={() => setShowRulesModal(false)}
                                        className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>
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
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2">
                                                        <h4 className="text-white font-medium">{rule.name}</h4>
                                                        <span className="text-xs px-2 py-0.5 rounded bg-gray-500/20 text-gray-400">
                                                            {rule.rule_type}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className={`text-xs px-2 py-0.5 rounded-full ${rule.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                                                        rule.severity === 'high' ? 'bg-orange-500/20 text-orange-400' :
                                                            rule.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                                                'bg-blue-500/20 text-blue-400'
                                                        }`}>
                                                        {rule.severity}
                                                    </span>
                                                    <span className="text-xs text-gray-400">Weight: {rule.weight}</span>
                                                    {!selectedStandard.is_builtin && (
                                                        <>
                                                            <button
                                                                onClick={() => handleEditRule(rule)}
                                                                className="p-1 text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors"
                                                            >
                                                                <Edit2 className="w-3.5 h-3.5" />
                                                            </button>
                                                            <button
                                                                onClick={() => handleDeleteRule(rule)}
                                                                className="p-1 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors"
                                                            >
                                                                <Trash2 className="w-3.5 h-3.5" />
                                                            </button>
                                                        </>
                                                    )}
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
                                    <p className="text-gray-400 mb-4">No rules defined for this standard</p>
                                    {!selectedStandard.is_builtin && (
                                        <button
                                            onClick={handleAddRule}
                                            className="inline-flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors"
                                        >
                                            <Plus className="w-5 h-5" />
                                            Add First Rule
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Rule Form Modal */}
            {showRuleModal && selectedStandard && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="bg-[#0A0F16] border border-white/10 rounded-xl w-full max-w-lg max-h-[90vh] overflow-hidden mx-4">
                        <div className="p-6 border-b border-white/10">
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-bold text-white">
                                    {editingRule ? 'Edit Rule' : 'Add New Rule'}
                                </h2>
                                <button
                                    onClick={() => setShowRuleModal(false)}
                                    className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                        <form onSubmit={handleRuleSubmit} className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
                            <div className="space-y-4">
                                {/* Name */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Name *</label>
                                    <input
                                        type="text"
                                        value={ruleFormData.name}
                                        onChange={(e) => setRuleFormData({ ...ruleFormData, name: e.target.value })}
                                        className="w-full px-3 py-2 bg-[#0F1419] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none"
                                        placeholder="e.g., Require README"
                                        required
                                    />
                                </div>

                                {/* Description */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
                                    <textarea
                                        value={ruleFormData.description}
                                        onChange={(e) => setRuleFormData({ ...ruleFormData, description: e.target.value })}
                                        className="w-full px-3 py-2 bg-[#0F1419] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none resize-none"
                                        rows={2}
                                        placeholder="What does this rule check for?"
                                    />
                                </div>

                                {/* Rule Type */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Rule Type *</label>
                                    <select
                                        value={ruleFormData.rule_type}
                                        onChange={(e) => {
                                            const newType = e.target.value;
                                            setRuleFormData({
                                                ...ruleFormData,
                                                rule_type: newType,
                                                check_config: {}
                                            });
                                        }}
                                        className="w-full px-3 py-2 bg-[#0F1419] border border-white/10 rounded-lg text-white focus:border-primary focus:outline-none"
                                    >
                                        {RULE_TYPES.map(type => (
                                            <option key={type.value} value={type.value}>{type.label}</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Config Fields based on rule type */}
                                <div className="bg-[#0F1419] border border-white/10 rounded-lg p-4">
                                    <label className="block text-sm font-medium text-gray-300 mb-3">Configuration</label>
                                    {ruleFormData.rule_type === 'file_exists' && (
                                        <input
                                            type="text"
                                            value={ruleFormData.check_config.path || ''}
                                            onChange={(e) => updateCheckConfig('path', e.target.value)}
                                            className="w-full px-3 py-2 bg-[#0A0F16] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none"
                                            placeholder="File path, e.g., README.md"
                                        />
                                    )}
                                    {ruleFormData.rule_type === 'file_forbidden' && (
                                        <input
                                            type="text"
                                            value={ruleFormData.check_config.pattern || ruleFormData.check_config.path || ''}
                                            onChange={(e) => updateCheckConfig('pattern', e.target.value)}
                                            className="w-full px-3 py-2 bg-[#0A0F16] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none"
                                            placeholder="File pattern, e.g., *.env or .env"
                                        />
                                    )}
                                    {ruleFormData.rule_type === 'folder_exists' && (
                                        <input
                                            type="text"
                                            value={ruleFormData.check_config.path || ''}
                                            onChange={(e) => updateCheckConfig('path', e.target.value)}
                                            className="w-full px-3 py-2 bg-[#0A0F16] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none"
                                            placeholder="Folder path, e.g., src/"
                                        />
                                    )}
                                    {ruleFormData.rule_type === 'pattern_match' && (
                                        <div className="space-y-2">
                                            <input
                                                type="text"
                                                value={ruleFormData.check_config.pattern || ''}
                                                onChange={(e) => updateCheckConfig('pattern', e.target.value)}
                                                className="w-full px-3 py-2 bg-[#0A0F16] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none"
                                                placeholder="Pattern to search for"
                                            />
                                            <label className="flex items-center gap-2 text-sm text-gray-400">
                                                <input
                                                    type="checkbox"
                                                    checked={ruleFormData.check_config.should_exist !== false}
                                                    onChange={(e) => updateCheckConfig('should_exist', e.target.checked)}
                                                    className="checkbox checkbox-sm checkbox-primary"
                                                />
                                                Pattern should exist
                                            </label>
                                        </div>
                                    )}
                                    {ruleFormData.rule_type === 'config_check' && (
                                        <div className="space-y-2">
                                            <input
                                                type="text"
                                                value={ruleFormData.check_config.file || ''}
                                                onChange={(e) => updateCheckConfig('file', e.target.value)}
                                                className="w-full px-3 py-2 bg-[#0A0F16] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none"
                                                placeholder="Config file, e.g., package.json"
                                            />
                                            <input
                                                type="text"
                                                value={ruleFormData.check_config.key || ''}
                                                onChange={(e) => updateCheckConfig('key', e.target.value)}
                                                className="w-full px-3 py-2 bg-[#0A0F16] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none"
                                                placeholder="Key to check, e.g., scripts.test"
                                            />
                                            <input
                                                type="text"
                                                value={ruleFormData.check_config.expected_value || ''}
                                                onChange={(e) => updateCheckConfig('expected_value', e.target.value)}
                                                className="w-full px-3 py-2 bg-[#0A0F16] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none"
                                                placeholder="Expected value (optional)"
                                            />
                                        </div>
                                    )}
                                    {ruleFormData.rule_type === 'hygiene' && (
                                        <select
                                            value={ruleFormData.check_config.check_type || ''}
                                            onChange={(e) => updateCheckConfig('check_type', e.target.value)}
                                            className="w-full px-3 py-2 bg-[#0A0F16] border border-white/10 rounded-lg text-white focus:border-primary focus:outline-none"
                                        >
                                            <option value="">Select check type</option>
                                            <option value="branch_protection">Branch Protection</option>
                                            <option value="code_owners">Code Owners</option>
                                            <option value="ci_config">CI Configuration</option>
                                            <option value="gitignore">Gitignore Present</option>
                                        </select>
                                    )}
                                </div>

                                {/* Severity */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-1">Severity</label>
                                        <select
                                            value={ruleFormData.severity}
                                            onChange={(e) => setRuleFormData({ ...ruleFormData, severity: e.target.value })}
                                            className="w-full px-3 py-2 bg-[#0F1419] border border-white/10 rounded-lg text-white focus:border-primary focus:outline-none"
                                        >
                                            {SEVERITY_OPTIONS.map(sev => (
                                                <option key={sev} value={sev}>{sev.charAt(0).toUpperCase() + sev.slice(1)}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-300 mb-1">Weight</label>
                                        <input
                                            type="number"
                                            min="1"
                                            max="100"
                                            value={ruleFormData.weight}
                                            onChange={(e) => setRuleFormData({ ...ruleFormData, weight: parseInt(e.target.value) || 10 })}
                                            className="w-full px-3 py-2 bg-[#0F1419] border border-white/10 rounded-lg text-white focus:border-primary focus:outline-none"
                                        />
                                    </div>
                                </div>

                                {/* Remediation Hint */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Remediation Hint</label>
                                    <textarea
                                        value={ruleFormData.remediation_hint}
                                        onChange={(e) => setRuleFormData({ ...ruleFormData, remediation_hint: e.target.value })}
                                        className="w-full px-3 py-2 bg-[#0F1419] border border-white/10 rounded-lg text-white placeholder-gray-400 focus:border-primary focus:outline-none resize-none"
                                        rows={2}
                                        placeholder="How to fix this if it fails?"
                                    />
                                </div>
                            </div>

                            <div className="flex gap-3 justify-end mt-6">
                                <button
                                    type="button"
                                    onClick={() => setShowRuleModal(false)}
                                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                                    disabled={savingRule}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors disabled:opacity-50"
                                    disabled={savingRule}
                                >
                                    {savingRule ? 'Saving...' : (editingRule ? 'Save Changes' : 'Add Rule')}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Standards;

