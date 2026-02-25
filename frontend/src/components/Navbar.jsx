import { Link } from 'react-router-dom';

export default function Navbar({ sessionLabel }) {
    return (
        <nav className="navbar">
            <Link to="/" className="navbar__brand" style={{ textDecoration: 'none' }}>
                <span className="accent">F1</span> Sector Analysis
            </Link>
            {sessionLabel && (
                <div className="navbar__session">
                    <span style={{ color: '#E10600', marginRight: 6 }}>●</span>
                    {sessionLabel}
                </div>
            )}
        </nav>
    );
}
