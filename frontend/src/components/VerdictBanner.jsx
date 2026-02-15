import { formatLapTime, formatDelta } from '../utils/formatTime';

export default function VerdictBanner({ comparison }) {
    const {
        driver1, driver2, color1, color2,
        overall_time1, overall_time2, overall_delta, overall_faster,
        sectors, lap1_num, lap2_num,
    } = comparison;

    const sectorsWon1 = sectors.filter(s => s.faster === driver1).length;
    const sectorsWon2 = sectors.filter(s => s.faster === driver2).length;
    const isTie = overall_faster === 'TIE';
    const winnerColor = overall_faster === driver1 ? color1 : color2;

    return (
        <div
            className="verdict-banner scale-in"
            style={{ '--winner-color': isTie ? '#FFD700' : winnerColor }}
        >
            <div className="verdict-banner__winner" style={{ color: isTie ? '#FFD700' : winnerColor }}>
                {isTie ? '⚡ DEAD HEAT ⚡' : `${overall_faster} FASTER`}
            </div>
            {!isTie && (
                <div style={{
                    fontSize: '2.2rem',
                    fontWeight: 900,
                    color: winnerColor,
                    letterSpacing: '2px',
                    marginBottom: 8,
                    fontVariantNumeric: 'tabular-nums',
                }}>
                    {formatDelta(overall_delta).replace(/^[+-]/, '')}
                </div>
            )}
            <div className="verdict-banner__delta">
                <span style={{ color: color1, fontWeight: 600 }}>{driver1}</span>
                {' '}
                {formatLapTime(overall_time1)}
                <span style={{ color: '#444', margin: '0 12px' }}>|</span>
                <span style={{ color: color2, fontWeight: 600 }}>{driver2}</span>
                {' '}
                {formatLapTime(overall_time2)}
            </div>
            <div className="verdict-banner__sectors">
                Sectors won:
                <span style={{ color: color1, fontWeight: 700, margin: '0 4px' }}>{sectorsWon1}</span>
                –
                <span style={{ color: color2, fontWeight: 700, margin: '0 4px' }}>{sectorsWon2}</span>
            </div>
        </div>
    );
}
