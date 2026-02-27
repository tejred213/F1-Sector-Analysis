import {
    LineChart,
    Line,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
} from 'recharts';

// ─── Shared chart configuration ──────────────────────────────────────────────
const SECTOR_LINES = [
    { x: 33.3, label: 'S1' },
    { x: 66.6, label: 'S2' },
];

const CHART_MARGIN = { top: 6, right: 12, left: 0, bottom: 0 };
const GRID_COLOR   = 'rgba(255,255,255,0.07)';
const TICK_STYLE   = { fill: '#666', fontSize: 11 };

function SectorRefs() {
    return SECTOR_LINES.map(({ x, label }) => (
        <ReferenceLine
            key={label}
            x={x}
            stroke="rgba(255,255,255,0.12)"
            strokeDasharray="4 3"
            label={{ value: label, position: 'insideTopLeft', fill: '#555', fontSize: 10 }}
        />
    ));
}

// ─── Custom shared tooltip ────────────────────────────────────────────────────
function sharedTooltip(d1, d2, formatter) {
    return (
        <Tooltip
            contentStyle={{
                backgroundColor: 'rgba(15,15,20,0.95)',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '8px',
                padding: '8px 12px',
            }}
            itemStyle={{ fontSize: '13px', fontWeight: 600, padding: '1px 0' }}
            labelStyle={{ display: 'none' }}
            formatter={formatter ?? ((value, name) => [
                value,
                name.includes('1') ? d1 : d2,
            ])}
        />
    );
}

// ─── Panel wrapper ────────────────────────────────────────────────────────────
function Panel({ label, unit, height = 110, children }) {
    return (
        <div className="telemetry-panel">
            <div className="telemetry-panel-label">
                <span className="telemetry-panel-name">{label}</span>
                {unit && <span className="telemetry-panel-unit">{unit}</span>}
            </div>
            <div className="telemetry-panel-chart" style={{ height }}>
                {children}
            </div>
        </div>
    );
}

// ─── Main component ───────────────────────────────────────────────────────────
export default function TelemetryCharts({ data }) {
    if (!data || !data.speed1 || !data.speed2) return null;

    const N    = data.speed1.length;
    const d1   = data.driver1;
    const d2   = data.driver2;
    const c1   = data.color1;
    const c2   = data.color2;

    // Build unified chart data array (200 points, 0–100% distance)
    const chartData = Array.from({ length: N }, (_, i) => ({
        pct:      parseFloat(((i / (N - 1)) * 100).toFixed(2)),
        speed1:   data.speed1[i]    ?? 0,
        speed2:   data.speed2[i]    ?? 0,
        rpm1:     (data.rpm1?.[i]   ?? 0) / 1000,   // display as k-RPM
        rpm2:     (data.rpm2?.[i]   ?? 0) / 1000,
        gear1:    data.gear1?.[i]   ?? 0,
        gear2:    data.gear2?.[i]   ?? 0,
        // Throttle 0–100 %, Brake 0/1 boolean → scale to 100 for overlay
        throttle1: data.throttle1?.[i] ?? 0,
        throttle2: data.throttle2?.[i] ?? 0,
        brake1:   (data.brake1?.[i] ?? 0) * 100,
        brake2:   (data.brake2?.[i] ?? 0) * 100,
        // DRS: 10/12 = active, 0 = closed  → normalise to 0 or 1
        drs1: (data.drs1?.[i] ?? 0) >= 10 ? 1 : 0,
        drs2: (data.drs2?.[i] ?? 0) >= 10 ? 1 : 0,
    }));

    const allSpeeds  = [...data.speed1, ...data.speed2];
    const minSpeed   = Math.floor(Math.min(...allSpeeds) / 20) * 20;
    const maxSpeed   = Math.ceil(Math.max(...allSpeeds)  / 20) * 20;

    const allRpms    = [...(data.rpm1 ?? []), ...(data.rpm2 ?? [])].map(v => v / 1000);
    const maxRpm     = Math.ceil(Math.max(...allRpms, 1) * 1.05);

    // Shared X-axis (only shown on the last panel)
    const xAxisShared = (show = false) => (
        <XAxis
            dataKey="pct"
            type="number"
            domain={[0, 100]}
            hide={!show}
            tickLine={false}
            axisLine={false}
            tick={show ? { ...TICK_STYLE } : false}
            tickFormatter={v => `${Math.round(v)}%`}
        />
    );

    return (
        <div className="telemetry-section fade-in stagger-4">
            {/* Driver legend */}
            <div className="telemetry-legend-row">
                <span className="telemetry-legend-badge" style={{ borderColor: c1 }}>
                    <span className="telemetry-legend-dot" style={{ background: c1 }} />
                    {d1}
                </span>
                <span className="telemetry-legend-badge" style={{ borderColor: c2 }}>
                    <span className="telemetry-legend-dot" style={{ background: c2 }} />
                    {d2}
                </span>
            </div>

            <div className="telemetry-charts-stack">

                {/* ── 1. Speed ─────────────────────────────────────────── */}
                <Panel label="SPEED" unit="km/h" height={130}>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={CHART_MARGIN}>
                            <CartesianGrid vertical={false} stroke={GRID_COLOR} />
                            {xAxisShared(false)}
                            <YAxis domain={[minSpeed, maxSpeed]} tick={TICK_STYLE} tickLine={false} axisLine={false} width={38} />
                            {sharedTooltip(d1, d2, (v, name) => [`${Math.round(v)} km/h`, name.includes('1') ? d1 : d2])}
                            <SectorRefs />
                            <Line type="monotone" dataKey="speed1" stroke={c1} strokeWidth={2} dot={false} activeDot={{ r: 5, strokeWidth: 0 }} isAnimationActive={false} />
                            <Line type="monotone" dataKey="speed2" stroke={c2} strokeWidth={2} dot={false} activeDot={{ r: 5, strokeWidth: 0 }} isAnimationActive={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </Panel>

                {/* ── 2. RPM ───────────────────────────────────────────── */}
                <Panel label="RPM" unit="×1000" height={100}>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={CHART_MARGIN}>
                            <CartesianGrid vertical={false} stroke={GRID_COLOR} />
                            {xAxisShared(false)}
                            <YAxis domain={[0, maxRpm]} tick={TICK_STYLE} tickLine={false} axisLine={false} width={38} tickFormatter={v => v.toFixed(1)} />
                            {sharedTooltip(d1, d2, (v, name) => [`${(v).toFixed(1)}k`, name.includes('1') ? d1 : d2])}
                            <SectorRefs />
                            <Line type="monotone" dataKey="rpm1" stroke={c1} strokeWidth={1.8} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} isAnimationActive={false} />
                            <Line type="monotone" dataKey="rpm2" stroke={c2} strokeWidth={1.8} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} isAnimationActive={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </Panel>

                {/* ── 3. Gear ──────────────────────────────────────────── */}
                <Panel label="GEAR" unit="" height={90}>
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={CHART_MARGIN}>
                            <CartesianGrid vertical={false} stroke={GRID_COLOR} />
                            {xAxisShared(false)}
                            <YAxis domain={[1, 8]} ticks={[1,2,3,4,5,6,7,8]} tick={TICK_STYLE} tickLine={false} axisLine={false} width={38} />
                            {sharedTooltip(d1, d2, (v, name) => [`Gear ${Math.round(v)}`, name.includes('1') ? d1 : d2])}
                            <SectorRefs />
                            <Line type="stepAfter" dataKey="gear1" stroke={c1} strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} isAnimationActive={false} />
                            <Line type="stepAfter" dataKey="gear2" stroke={c2} strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} isAnimationActive={false} strokeDasharray="5 3" />
                        </LineChart>
                    </ResponsiveContainer>
                </Panel>

                {/* ── 4. Throttle + Brake ───────────────────────────────── */}
                <Panel label="THROTTLE / BRAKE" unit="%" height={110}>
                    <div className="telemetry-dual-row">
                        {/* Driver 1 */}
                        <div className="telemetry-dual-half">
                            <span className="telemetry-dual-name" style={{ color: c1 }}>{d1}</span>
                            <ResponsiveContainer width="100%" height={80}>
                                <AreaChart data={chartData} margin={{ ...CHART_MARGIN, left: -8 }}>
                                    <CartesianGrid vertical={false} stroke={GRID_COLOR} />
                                    {xAxisShared(false)}
                                    <YAxis domain={[0, 100]} hide />
                                    {sharedTooltip(d1, d2, (v, name) => [
                                        `${Math.round(v)}%`,
                                        name === 'throttle1' ? 'Throttle' : 'Brake'
                                    ])}
                                    <SectorRefs />
                                    <Area type="monotone" dataKey="throttle1" stroke="#26d07c" fill="#26d07c" fillOpacity={0.35} strokeWidth={1.5} dot={false} isAnimationActive={false} />
                                    <Area type="monotone" dataKey="brake1"    stroke="#e53935" fill="#e53935" fillOpacity={0.4}  strokeWidth={1.5} dot={false} isAnimationActive={false} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                        {/* Driver 2 */}
                        <div className="telemetry-dual-half">
                            <span className="telemetry-dual-name" style={{ color: c2 }}>{d2}</span>
                            <ResponsiveContainer width="100%" height={80}>
                                <AreaChart data={chartData} margin={{ ...CHART_MARGIN, left: -8 }}>
                                    <CartesianGrid vertical={false} stroke={GRID_COLOR} />
                                    {xAxisShared(false)}
                                    <YAxis domain={[0, 100]} hide />
                                    {sharedTooltip(d1, d2, (v, name) => [
                                        `${Math.round(v)}%`,
                                        name === 'throttle2' ? 'Throttle' : 'Brake'
                                    ])}
                                    <SectorRefs />
                                    <Area type="monotone" dataKey="throttle2" stroke="#26d07c" fill="#26d07c" fillOpacity={0.35} strokeWidth={1.5} dot={false} isAnimationActive={false} />
                                    <Area type="monotone" dataKey="brake2"    stroke="#e53935" fill="#e53935" fillOpacity={0.4}  strokeWidth={1.5} dot={false} isAnimationActive={false} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </Panel>

                {/* ── 5. DRS ───────────────────────────────────────────── */}
                <Panel label="DRS" unit="" height={90}>
                    <div className="telemetry-dual-row telemetry-dual-row--drs">
                        {/* Driver 1 DRS */}
                        <div className="telemetry-dual-half">
                            <span className="telemetry-dual-name" style={{ color: c1 }}>{d1}</span>
                            <ResponsiveContainer width="100%" height={45}>
                                <AreaChart data={chartData} margin={{ ...CHART_MARGIN, left: -8, top: 2 }}>
                                    {xAxisShared(false)}
                                    <YAxis domain={[0, 1]} hide />
                                    <SectorRefs />
                                    <Area type="stepAfter" dataKey="drs1" stroke={c1} fill={c1} fillOpacity={0.5} strokeWidth={0} dot={false} isAnimationActive={false} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                        {/* Driver 2 DRS */}
                        <div className="telemetry-dual-half">
                            <span className="telemetry-dual-name" style={{ color: c2 }}>{d2}</span>
                            <ResponsiveContainer width="100%" height={45}>
                                <AreaChart data={chartData} margin={{ ...CHART_MARGIN, left: -8, top: 2 }}>
                                    {xAxisShared(false)}
                                    <YAxis domain={[0, 1]} hide />
                                    <SectorRefs />
                                    <Area type="stepAfter" dataKey="drs2" stroke={c2} fill={c2} fillOpacity={0.5} strokeWidth={0} dot={false} isAnimationActive={false} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Shared X-axis distance labels at the very bottom */}
                    <div className="telemetry-xaxis-label">
                        {[0, 25, 50, 75, 100].map(v => (
                            <span key={v} style={{ flex: v === 0 ? 0 : 1, textAlign: v === 100 ? 'right' : 'center' }}>
                                {v}%
                            </span>
                        ))}
                    </div>
                </Panel>

            </div>

            {/* Throttle/Brake legend */}
            <div className="telemetry-tb-legend">
                <span><span className="telemetry-tb-dot" style={{ background: '#26d07c' }} />Throttle</span>
                <span><span className="telemetry-tb-dot" style={{ background: '#e53935' }} />Brake</span>
                <span style={{ color: '#555', fontSize: '11px', marginLeft: '8px' }}>DRS = open zone</span>
            </div>
        </div>
    );
}
