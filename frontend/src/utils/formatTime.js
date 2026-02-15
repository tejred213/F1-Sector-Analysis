/**
 * Format seconds into race lap time format: M:SS.mmm
 * e.g. 82.109 → "1:22.109"
 *      29.613 → "29.613"  (under 60s, no minute prefix)
 */
export function formatLapTime(seconds) {
    if (seconds == null || isNaN(seconds)) return '—';
    const mins = Math.floor(seconds / 60);
    const secs = seconds - mins * 60;
    if (mins > 0) {
        return `${mins}:${secs.toFixed(3).padStart(6, '0')}`;
    }
    return secs.toFixed(3);
}

/**
 * Format a delta (difference in seconds): +0.371 or -0.182
 * Always shows sign, uses M:SS.mmm if ≥ 60s
 */
export function formatDelta(delta) {
    if (delta == null || isNaN(delta)) return '—';
    const abs = Math.abs(delta);
    const sign = delta > 0 ? '+' : delta < 0 ? '-' : '';
    const mins = Math.floor(abs / 60);
    const secs = abs - mins * 60;
    if (mins > 0) {
        return `${sign}${mins}:${secs.toFixed(3).padStart(6, '0')}`;
    }
    return `${sign}${secs.toFixed(3)}`;
}
