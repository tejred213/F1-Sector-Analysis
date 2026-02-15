import { useState, useEffect } from 'react';

export default function SpeedTraps({ comparison }) {
    const { driver1, driver2, color1, color2, speed_traps } = comparison;
    const [animate, setAnimate] = useState(false);

    useEffect(() => {
        // Trigger bar animation after mount
        const timer = setTimeout(() => setAnimate(true), 100);
        return () => clearTimeout(timer);
    }, [comparison]);

    return (
        <div className="speed-traps-grid">
            {speed_traps.map((trap, i) => {
                const maxSpeed = Math.max(trap.speed1, trap.speed2);
                const minForScale = maxSpeed * 0.85;
                const range = maxSpeed - minForScale;
                const pct1 = ((trap.speed1 - minForScale) / range) * 100;
                const pct2 = ((trap.speed2 - minForScale) / range) * 100;
                const d1Faster = trap.faster === driver1;
                const d2Faster = trap.faster === driver2;

                return (
                    <div
                        className="speed-card fade-in"
                        key={i}
                        style={{ animationDelay: `${0.1 * (i + 1)}s` }}
                    >
                        <div className="speed-card__label">{trap.trap}</div>

                        <div className="speed-bar-row">
                            <div className="speed-bar-row__driver" style={{ color: d1Faster ? color1 : 'inherit' }}>
                                {driver1}
                            </div>
                            <div className="speed-bar-row__bar-container">
                                <div
                                    className="speed-bar-row__bar"
                                    style={{
                                        width: animate ? `${Math.max(pct1, 3)}%` : '0%',
                                        background: `linear-gradient(90deg, ${color1}, ${color1}cc)`,
                                        opacity: d1Faster ? 1 : 0.45,
                                        transitionDelay: `${0.1 * i}s`,
                                    }}
                                />
                            </div>
                            <div className="speed-bar-row__value" style={{ color: d1Faster ? '#fff' : '#888' }}>
                                {Math.round(trap.speed1)}
                            </div>
                        </div>

                        <div className="speed-bar-row">
                            <div className="speed-bar-row__driver" style={{ color: d2Faster ? color2 : 'inherit' }}>
                                {driver2}
                            </div>
                            <div className="speed-bar-row__bar-container">
                                <div
                                    className="speed-bar-row__bar"
                                    style={{
                                        width: animate ? `${Math.max(pct2, 3)}%` : '0%',
                                        background: `linear-gradient(90deg, ${color2}, ${color2}cc)`,
                                        opacity: d2Faster ? 1 : 0.45,
                                        transitionDelay: `${0.1 * i + 0.05}s`,
                                    }}
                                />
                            </div>
                            <div className="speed-bar-row__value" style={{ color: d2Faster ? '#fff' : '#888' }}>
                                {Math.round(trap.speed2)}
                            </div>
                        </div>

                        <div className="speed-card__winner" style={{ color: trap.faster === driver1 ? color1 : color2 }}>
                            {trap.faster !== 'TIE'
                                ? `▲ ${trap.faster}  +${Math.abs(trap.delta)} km/h`
                                : 'TIE'}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
