import { formatLapTime, formatDelta } from '../utils/formatTime';

export default function SectorCards({ comparison }) {
    const { driver1, driver2, color1, color2, sectors } = comparison;

    return (
        <div className="sectors-grid">
            {sectors.map((s, i) => {
                const d1Faster = s.faster === driver1;
                const d2Faster = s.faster === driver2;

                return (
                    <div
                        className="sector-card fade-in"
                        key={i}
                        style={{ animationDelay: `${0.08 * (i + 1)}s` }}
                    >
                        <div className="sector-card__label">{s.sector}</div>

                        <div className="sector-card__row">
                            <div className="sector-card__driver">
                                <span className="dot" style={{ background: color1, color: color1 }} />
                                {driver1}
                            </div>
                            <div className={`sector-card__time ${d1Faster ? 'fastest' : ''}`}>
                                {formatLapTime(s.time1)}
                            </div>
                        </div>

                        <div className="sector-card__row">
                            <div className="sector-card__driver">
                                <span className="dot" style={{ background: color2, color: color2 }} />
                                {driver2}
                            </div>
                            <div className={`sector-card__time ${d2Faster ? 'fastest' : ''}`}>
                                {formatLapTime(s.time2)}
                            </div>
                        </div>

                        <div className="sector-card__delta">
                            <span className={`delta-badge ${s.delta < 0 ? 'negative' : 'positive'}`}>
                                {s.delta < 0 ? '◀ ' : ''}{formatDelta(s.delta)}{s.delta > 0 ? ' ▶' : ''}
                            </span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
