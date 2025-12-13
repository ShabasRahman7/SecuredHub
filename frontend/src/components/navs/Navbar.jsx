import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Menu, Sun, Moon, LogOut, User, Settings, LayoutDashboard } from 'lucide-react';

const Navbar = ({ title }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [theme, setTheme] = useState(localStorage.getItem('theme') || 'forest');

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme(theme === 'forest' ? 'pastel' : 'forest');
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="navbar bg-base-100 shadow-lg rounded-box mb-8">
            <div className="navbar-start">
                <div className="dropdown">
                    <div tabIndex={0} role="button" className="btn btn-ghost lg:hidden">
                        <Menu className="h-5 w-5" />
                    </div>
                    <ul tabIndex={0} className="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52">
                        <li><Link to="/"><LayoutDashboard className="w-4 h-4" /> Dashboard</Link></li>
                        <li><a><Settings className="w-4 h-4" /> Settings</a></li>
                        <li><a onClick={handleLogout}><LogOut className="w-4 h-4" /> Logout</a></li>
                    </ul>
                </div>
                <a className="btn btn-ghost text-xl">{title || 'SecuredHub'}</a>
            </div>

            <div className="navbar-center hidden lg:flex">
                <ul className="menu menu-horizontal px-1">
                    <li><Link to="/">Dashboard</Link></li>
                    <li><a>Settings</a></li>
                </ul>
            </div>

            <div className="navbar-end gap-2">
                {/* Theme Toggle */}
                <label className="swap swap-rotate btn btn-ghost btn-circle">
                    <input
                        type="checkbox"
                        onChange={toggleTheme}
                        checked={theme === 'pastel'}
                    />

                    {/* sun icon */}
                    <Sun className="swap-on fill-current w-6 h-6" />

                    {/* moon icon */}
                    <Moon className="swap-off fill-current w-6 h-6" />
                </label>

                <div className="dropdown dropdown-end">
                    <div tabIndex={0} role="button" className="btn btn-ghost btn-circle avatar">
                        <div className="w-10 rounded-full">
                            <img alt="User Avatar" src={`https://ui-avatars.com/api/?name=${user?.first_name || 'User'}&background=random`} />
                        </div>
                    </div>
                    <ul tabIndex={0} className="mt-3 z-[1] p-2 shadow menu menu-sm dropdown-content bg-base-100 rounded-box w-52">
                        <li>
                            <a className="justify-between">
                                Profile
                                <span className="badge">New</span>
                            </a>
                        </li>
                        <li><a>Settings</a></li>
                        <li><a onClick={handleLogout}>Logout</a></li>
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default Navbar;
