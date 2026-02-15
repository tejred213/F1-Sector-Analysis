export default function Navbar({ sessionLabel }) {
    return (
        <nav className="navbar">
            <div className="navbar__brand">
                <span className="accent">F1</span> Sector Analysis
            </div>
            {sessionLabel && (
                <div className="navbar__session">
                    <span style={{ color: '#E10600', marginRight: 6 }}>●</span>
                    {sessionLabel}
                </div>
            )}
        </nav>
    );
}
