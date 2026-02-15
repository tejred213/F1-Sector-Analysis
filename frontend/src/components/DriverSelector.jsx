export default function DriverSelector({
    drivers, d1, d2, setD1, setD2,
    lap1, lap2, setLap1, setLap2,
    getDriverInfo,
}) {
    const info1 = getDriverInfo(d1);
    const info2 = getDriverInfo(d2);

    return (
        <div className="selector-row">
            {/* Driver 1 */}
            <div
                className="driver-card"
                style={{ '--driver-color': info1?.color || '#E10600' }}
            >
                <div className="driver-card__info">
                    <div className="driver-card__abbr" style={{ color: info1?.color }}>
                        {d1 || '---'}
                    </div>
                    <div className="driver-card__team">{info1?.team || 'Select a driver'}</div>
                    <div className="driver-card__lap-select">
                        <select value={d1} onChange={e => { setD1(e.target.value); setLap1(''); }}>
                            <option value="">Select Driver</option>
                            {drivers.map(d => (
                                <option key={d.driver} value={d.driver}>{d.driver} — {d.team}</option>
                            ))}
                        </select>
                    </div>
                    {info1 && (
                        <div className="driver-card__lap-select" style={{ marginTop: 4 }}>
                            <select value={lap1} onChange={e => setLap1(e.target.value)}>
                                <option value="">Best Lap</option>
                                {info1.lapNumbers.map(n => (
                                    <option key={n} value={n}>Lap {n}</option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>
            </div>

            {/* VS badge */}
            <div className="vs-badge">VS</div>

            {/* Driver 2 */}
            <div
                className="driver-card"
                style={{ '--driver-color': info2?.color || '#E10600' }}
            >
                <div className="driver-card__info">
                    <div className="driver-card__abbr" style={{ color: info2?.color }}>
                        {d2 || '---'}
                    </div>
                    <div className="driver-card__team">{info2?.team || 'Select a driver'}</div>
                    <div className="driver-card__lap-select">
                        <select value={d2} onChange={e => { setD2(e.target.value); setLap2(''); }}>
                            <option value="">Select Driver</option>
                            {drivers.map(d => (
                                <option key={d.driver} value={d.driver}>{d.driver} — {d.team}</option>
                            ))}
                        </select>
                    </div>
                    {info2 && (
                        <div className="driver-card__lap-select" style={{ marginTop: 4 }}>
                            <select value={lap2} onChange={e => setLap2(e.target.value)}>
                                <option value="">Best Lap</option>
                                {info2.lapNumbers.map(n => (
                                    <option key={n} value={n}>Lap {n}</option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
