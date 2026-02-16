import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine
} from 'recharts';

export default function TelemetryCharts({ data }) {
    if (!data || !data.speed1 || !data.speed2) return null;

    // Transform parallel arrays into objects for Recharts
    // data.x contains distance points (resampled to 200 points)
    // We can assume data.speed1 and data.speed2 match this length
    const chartData = data.speed1.map((s1, i) => ({
        distance: i, // We use index as proxy for distance percent (0-200) or actual distance if available? 
        // Actually data.x is coordinate, not linear distance.
        // But in preprocess.py, we resampled to 200 points. 
        // Let's generate a percentage or just use index 0-100%
        distPct: (i / (data.speed1.length - 1)) * 100,
        speed1: s1,
        speed2: data.speed2[i],
    }));

    // Calculate domain for Y-axis to make chart look dynamic (don't start at 0 if min speed is 60)
    const allSpeeds = [...data.speed1, ...data.speed2];
    const minSpeed = Math.floor(Math.min(...allSpeeds) / 10) * 10;
    const maxSpeed = Math.ceil(Math.max(...allSpeeds) / 10) * 10;

    return (
        <div className="telemetry-section fade-in stagger-4">
            <div className="telemetry-container">
                <div className="telemetry-chart-wrapper">
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.1)" />

                            <XAxis
                                dataKey="distPct"
                                type="number"
                                hide={true}
                                domain={[0, 100]}
                            />

                            <YAxis
                                domain={[minSpeed - 20, maxSpeed + 10]}
                                stroke="#888"
                                tick={{ fill: '#888', fontSize: 12 }}
                                tickLine={false}
                                axisLine={false}
                            />

                            <Tooltip
                                contentStyle={{ backgroundColor: 'rgba(20, 20, 20, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                itemStyle={{ fontSize: '13px', fontWeight: 600 }}
                                labelStyle={{ display: 'none' }}
                                formatter={(value, name) => [
                                    `${Math.round(value)} km/h`,
                                    name === 'speed1' ? data.driver1 : data.driver2
                                ]}
                            />

                            <Line
                                type="monotone"
                                dataKey="speed1"
                                stroke={data.color1}
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 6, strokeWidth: 0 }}
                                animationDuration={1000}
                            />

                            <Line
                                type="monotone"
                                dataKey="speed2"
                                stroke={data.color2}
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 6, strokeWidth: 0 }}
                                animationDuration={1000}
                            />

                            {/* Sector Dividers (approximate at 33% and 66%) */}
                            <ReferenceLine x={33.3} stroke="rgba(255,255,255,0.1)" strokeDasharray="3 3" label={{ value: 'S1', position: 'insideTopLeft', fill: '#666', fontSize: 10 }} />
                            <ReferenceLine x={66.6} stroke="rgba(255,255,255,0.1)" strokeDasharray="3 3" label={{ value: 'S2', position: 'insideTopLeft', fill: '#666', fontSize: 10 }} />
                        </LineChart>
                    </ResponsiveContainer>
                    <div className="telemetry-legend">
                        <span style={{ color: '#888', fontSize: '12px' }}>Speed (km/h) vs Distance (%)</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
