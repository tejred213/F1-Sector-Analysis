import { useState, useEffect } from 'react';

const YEARS = [];
for (let y = 2025; y >= 2018; y--) YEARS.push(y);

export default function SessionSelector({ year, gp, setYear, setGp, onSessionLoaded }) {
    const [races, setRaces] = useState([]);
    const [loadingSchedule, setLoadingSchedule] = useState(false);

    // Fetch schedule whenever year changes
    useEffect(() => {
        setLoadingSchedule(true);
        setRaces([]);
        fetch(`/api/schedule?year=${year}`)
            .then(res => res.json())
            .then(data => {
                setRaces(data.races || []);
                // Auto-select the first race if current GP not in list
                if (data.races && data.races.length > 0) {
                    const names = data.races.map(r => r.name);
                    if (!names.includes(gp)) {
                        setGp(data.races[0].name);
                    }
                }
            })
            .catch(() => setRaces([]))
            .finally(() => setLoadingSchedule(false));
    }, [year]);

    return (
        <div className="session-selector">
            <div className="session-selector__label">SESSION</div>
            <div className="session-selector__controls">
                <div className="session-selector__group">
                    <label>Season</label>
                    <select value={year} onChange={e => setYear(Number(e.target.value))}>
                        {YEARS.map(y => (
                            <option key={y} value={y}>{y}</option>
                        ))}
                    </select>
                </div>

                <div className="session-selector__group">
                    <label>Grand Prix</label>
                    <select
                        value={gp}
                        onChange={e => setGp(e.target.value)}
                        disabled={loadingSchedule || races.length === 0}
                    >
                        {loadingSchedule && <option>Loading…</option>}
                        {races.map(r => (
                            <option key={r.round} value={r.name}>
                                R{r.round} — {r.name}
                            </option>
                        ))}
                    </select>
                </div>

                <button
                    className="session-selector__load-btn"
                    onClick={onSessionLoaded}
                    disabled={loadingSchedule || !gp}
                >
                    Load Session
                </button>
            </div>
        </div>
    );
}
