import React from 'react';
import { Link } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="navbar navbar--landing">
      <div className="navbar__container">
        <Link to="/" className="navbar__logo">
          <span className="logo-icon"></span>
          <span className="logo-text">APEX<span className="text-red">TELEMETRY</span></span>
        </Link>
      </div>
    </nav>
  );
}
