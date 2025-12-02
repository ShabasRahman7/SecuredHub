import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Layout, Sparkles, ArrowRight, CheckCircle, Lock, Terminal, MessageSquare } from 'lucide-react';

const LandingPage = () => {
    const [isMenuOpen, setIsMenuOpen] = React.useState(false);

    return (
        <div className="min-h-screen bg-base-100 font-sans selection:bg-primary selection:text-white">
            {/* Navbar */}
            <nav className="navbar fixed top-0 z-50 bg-base-100/80 backdrop-blur-lg border-b border-white/5 px-6 lg:px-12 h-20">
                <div className="navbar-start">
                    <div className="flex items-center gap-3">
                        <Shield className="w-8 h-8 text-primary fill-primary/20" />
                        <span className="text-xl font-bold tracking-tight text-white">SecuredHub</span>
                    </div>
                </div>
                <div className="navbar-center hidden lg:flex">
                    <ul className="menu menu-horizontal px-1 gap-8 text-sm font-medium text-gray-400">
                        <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                        <li><a href="#how-it-works" className="hover:text-white transition-colors">How it Works</a></li>
                        <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                    </ul>
                </div>
                <div className="navbar-end gap-4 hidden lg:flex">
                    <Link to="/request-access" className="btn btn-primary btn-sm h-10 px-6 rounded-lg font-semibold shadow-lg shadow-primary/25 hover:shadow-primary/40 border-none">
                        Sign Up
                    </Link>
                    <Link to="/login" className="btn btn-ghost btn-sm h-10 px-6 rounded-lg font-semibold bg-white/5 hover:bg-white/10 border border-white/10 text-white">
                        Log In
                    </Link>
                </div>

                {/* Mobile Menu Button */}
                <div className="navbar-end lg:hidden">
                    <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="btn btn-ghost btn-circle text-white">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={isMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h7"} />
                        </svg>
                    </button>
                </div>
            </nav>

            {/* Mobile Menu Dropdown */}
            {isMenuOpen && (
                <div className="fixed top-20 left-0 w-full bg-base-100 border-b border-white/5 z-40 lg:hidden p-4 flex flex-col gap-4 shadow-2xl">
                    <ul className="menu w-full text-base font-medium text-gray-400 gap-2">
                        <li><a href="#features" onClick={() => setIsMenuOpen(false)} className="hover:text-white">Features</a></li>
                        <li><a href="#how-it-works" onClick={() => setIsMenuOpen(false)} className="hover:text-white">How it Works</a></li>
                        <li><a href="#pricing" onClick={() => setIsMenuOpen(false)} className="hover:text-white">Pricing</a></li>
                    </ul>
                    <div className="flex flex-col gap-3 mt-2">
                        <Link to="/request-access" onClick={() => setIsMenuOpen(false)} className="btn btn-primary w-full">Sign Up</Link>
                        <Link to="/login" onClick={() => setIsMenuOpen(false)} className="btn btn-ghost w-full bg-white/5 border border-white/10 text-white">Log In</Link>
                    </div>
                </div>
            )}

            {/* Hero Section */}
            <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 px-6 overflow-hidden">
                {/* Background Gradients */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full max-w-7xl pointer-events-none">
                    <div className="absolute top-20 left-20 w-96 h-96 bg-primary/20 rounded-full blur-[128px] opacity-50" />
                    <div className="absolute bottom-20 right-20 w-96 h-96 bg-secondary/20 rounded-full blur-[128px] opacity-30" />
                </div>

                <div className="container mx-auto max-w-7xl relative z-10">
                    <div className="grid lg:grid-cols-2 gap-16 items-center">
                        <div className="space-y-8">
                            <h1 className="text-5xl lg:text-7xl font-bold leading-[1.1] tracking-tight text-white">
                                Automate and secure your entire <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">development lifecycle.</span>
                            </h1>
                            <p className="text-lg text-gray-400 leading-relaxed max-w-xl">
                                SecuredHub integrates seamlessly with your GitHub repositories to provide continuous, automated security scanning and centralized visibility across all your projects.
                            </p>
                            <div className="flex flex-wrap gap-4 pt-4">
                                <Link to="/request-access" className="btn btn-primary h-12 px-8 rounded-lg text-base font-semibold shadow-xl shadow-primary/20 hover:shadow-primary/40 border-none">
                                    Get Started Free
                                </Link>
                                <button className="btn btn-ghost h-12 px-8 rounded-lg text-base font-semibold bg-white/5 hover:bg-white/10 border border-white/10 text-white">
                                    Request a Demo
                                </button>
                            </div>
                        </div>

                        {/* Abstract 3D Visual */}
                        <div className="relative">
                            <div className="aspect-square rounded-3xl overflow-hidden border border-white/10 bg-white/5 backdrop-blur-sm shadow-2xl relative group">
                                <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent opacity-50" />

                                {/* Simulated Dashboard UI */}
                                <div className="absolute inset-4 bg-[#0A0F16] rounded-2xl border border-white/5 p-6 flex flex-col gap-4 shadow-inner">
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex gap-2">
                                            <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
                                            <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                                            <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
                                        </div>
                                        <div className="h-2 w-20 bg-white/10 rounded-full" />
                                    </div>

                                    {/* Scan Animation */}
                                    <div className="flex-1 relative overflow-hidden rounded-xl bg-black/40 border border-white/5 p-4 space-y-3">
                                        <div className="flex items-center gap-3 text-xs font-mono text-gray-400">
                                            <Terminal className="w-4 h-4 text-primary" />
                                            <span>Running security scan...</span>
                                        </div>
                                        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                                            <div className="h-full bg-primary w-2/3 animate-pulse" />
                                        </div>
                                        <div className="space-y-2 pt-2">
                                            <div className="flex items-center justify-between text-xs p-2 rounded bg-white/5 border border-white/5">
                                                <span className="text-gray-300">auth_service.py</span>
                                                <span className="text-green-400">Safe</span>
                                            </div>
                                            <div className="flex items-center justify-between text-xs p-2 rounded bg-red-500/10 border border-red-500/20">
                                                <span className="text-gray-300">db_config.js</span>
                                                <span className="text-red-400">Critical</span>
                                            </div>
                                            <div className="flex items-center justify-between text-xs p-2 rounded bg-white/5 border border-white/5">
                                                <span className="text-gray-300">api_routes.go</span>
                                                <span className="text-green-400">Safe</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Core Capabilities */}
            <section id="features" className="py-24 bg-[#0B1219]">
                <div className="container mx-auto max-w-7xl px-6">
                    <div className="text-center max-w-2xl mx-auto mb-16">
                        <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">Core Capabilities</h2>
                        <p className="text-gray-400">Everything you need to build, deploy, and manage secure applications at scale, all in one platform.</p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {[
                            {
                                icon: <CheckCircle className="w-6 h-6 text-primary" />,
                                title: "Automated Security Scanning",
                                desc: "Integrate SAST, DAST, and SCA scans directly into your CI/CD pipeline for early threat detection."
                            },
                            {
                                icon: <Layout className="w-6 h-6 text-primary" />,
                                title: "Multi-Tenant Visibility",
                                desc: "Get a centralized dashboard for admins and isolated, secure views for individual teams and projects."
                            },
                            {
                                icon: <Sparkles className="w-6 h-6 text-primary" />,
                                title: "AI-Powered Remediation",
                                desc: "Leverage our RAG-powered assistant for fast, context-aware vulnerability explanations and fixes."
                            }
                        ].map((feature, idx) => (
                            <div key={idx} className="p-8 rounded-2xl bg-white/5 border border-white/5 hover:border-primary/30 transition-colors group">
                                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-6 group-hover:bg-primary/20 transition-colors">
                                    {feature.icon}
                                </div>
                                <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                                <p className="text-gray-400 leading-relaxed text-sm">{feature.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* How It Works */}
            <section id="how-it-works" className="py-24 relative overflow-hidden">
                <div className="container mx-auto max-w-7xl px-6">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">How It Works</h2>
                    </div>

                    <div className="relative">
                        {/* Connecting Line */}
                        <div className="absolute top-1/2 left-0 w-full h-0.5 bg-white/10 -translate-y-1/2 hidden md:block" />

                        <div className="grid md:grid-cols-3 gap-12 relative z-10">
                            {[
                                { step: "Step 1", title: "Connect Your Repository", icon: <Lock className="w-5 h-5" /> },
                                { step: "Step 2", title: "Scan & Analyze", icon: <Shield className="w-5 h-5" /> },
                                { step: "Step 3", title: "Remediate with AI", icon: <Sparkles className="w-5 h-5" /> }
                            ].map((item, idx) => (
                                <div key={idx} className="flex flex-col items-center text-center group">
                                    <div className="w-16 h-16 rounded-full bg-[#0A0F16] border border-white/10 flex items-center justify-center mb-6 relative z-10 group-hover:border-primary/50 group-hover:shadow-[0_0_30px_-5px_rgba(19,109,236,0.3)] transition-all duration-300">
                                        <div className="text-primary">{item.icon}</div>
                                    </div>
                                    <span className="text-xs font-mono text-primary mb-2">{item.step}</span>
                                    <h3 className="text-lg font-bold text-white">{item.title}</h3>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* AI Assistant Section */}
            <section className="py-24 bg-[#0B1219]">
                <div className="container mx-auto max-w-4xl px-6">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl lg:text-4xl font-bold text-white mb-4">Your AI Security Assistant</h2>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-[#0A0F16] p-1 shadow-2xl">
                        <div className="rounded-xl bg-[#0F1620] overflow-hidden">
                            {/* Chat Header */}
                            <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3 bg-white/5">
                                <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
                                    <Sparkles className="w-4 h-4 text-primary" />
                                </div>
                                <div>
                                    <h4 className="text-sm font-bold text-white">Secured AI</h4>
                                    <p className="text-xs text-gray-400">Always active</p>
                                </div>
                            </div>

                            {/* Chat Messages */}
                            <div className="p-6 space-y-6">
                                {/* User Message */}
                                <div className="flex gap-4">
                                    <div className="w-8 h-8 rounded-full bg-gray-700 flex-shrink-0 flex items-center justify-center text-xs font-bold text-white">U</div>
                                    <div className="bg-white/5 rounded-2xl rounded-tl-none p-4 max-w-lg border border-white/5">
                                        <p className="text-sm text-gray-300">Explain this SQL injection vulnerability in `user_controller.rb` and suggest a fix.</p>
                                    </div>
                                </div>

                                {/* AI Response */}
                                <div className="flex gap-4 flex-row-reverse">
                                    <div className="w-8 h-8 rounded-full bg-primary/20 flex-shrink-0 flex items-center justify-center">
                                        <Sparkles className="w-4 h-4 text-primary" />
                                    </div>
                                    <div className="bg-primary/10 rounded-2xl rounded-tr-none p-4 max-w-lg border border-primary/20">
                                        <p className="text-sm text-gray-200 mb-3">
                                            This SQL injection occurs because user input is directly concatenated into a database query. To fix this, use parameterized queries to separate the SQL code from user-provided data.
                                        </p>
                                        <div className="bg-black/50 rounded p-3 font-mono text-xs border border-white/5">
                                            <div className="text-red-400 line-through opacity-70">{'- User.where("id = #{params[:id]}")'}</div>
                                            <div className="text-green-400">{'+ User.where("id = ?", params[:id])'}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="border-t border-white/5 py-12 bg-[#0A0F16]">
                <div className="container mx-auto max-w-7xl px-6">
                    <div className="grid md:grid-cols-4 gap-12 mb-12">
                        <div className="col-span-1">
                            <div className="flex items-center gap-2 mb-6">
                                <Shield className="w-6 h-6 text-primary" />
                                <span className="text-lg font-bold text-white">SecuredHub</span>
                            </div>
                            <p className="text-sm text-gray-400">Automated DevSecOps for modern development teams.</p>
                        </div>

                        {[
                            { title: "Product", links: ["Features", "Pricing", "Integrations"] },
                            { title: "Resources", links: ["Documentation", "Blog", "Support"] },
                            { title: "Company", links: ["About Us", "Careers", "Contact"] }
                        ].map((col, idx) => (
                            <div key={idx}>
                                <h4 className="text-white font-bold mb-6">{col.title}</h4>
                                <ul className="space-y-4 text-sm text-gray-400">
                                    {col.links.map((link, lIdx) => (
                                        <li key={lIdx}><a href="#" className="hover:text-primary transition-colors">{link}</a></li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>

                    <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-gray-500">
                        <p>© 2024 SecurED-Hub. All rights reserved.</p>
                        <div className="flex gap-8">
                            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
                            <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
