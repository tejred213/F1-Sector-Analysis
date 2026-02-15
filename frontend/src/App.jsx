import { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import SessionSelector from './components/SessionSelector';
import DriverSelector from './components/DriverSelector';
import SectorCards from './components/SectorCards';
import TrackDominance from './components/TrackDominance';
import SpeedTraps from './components/SpeedTraps';
import VerdictBanner from './components/VerdictBanner';

function App() {
  // Session state
  const [year, setYear] = useState(2024);
  const [gp, setGp] = useState('');
  const [sessionLabel, setSessionLabel] = useState('');

  // Driver state
  const [drivers, setDrivers] = useState([]);
  const [d1, setD1] = useState('');
  const [d2, setD2] = useState('');
  const [lap1, setLap1] = useState('');
  const [lap2, setLap2] = useState('');

  // Results state
  const [comparison, setComparison] = useState(null);
  const [trackData, setTrackData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingDrivers, setLoadingDrivers] = useState(false);
  const [loadProgress, setLoadProgress] = useState('');
  const [error, setError] = useState('');

  // Load drivers for the selected session using background loading
  const loadDrivers = useCallback(async () => {
    if (!gp) return;
    setLoadingDrivers(true);
    setError('');
    setDrivers([]);
    setComparison(null);
    setTrackData(null);
    setD1('');
    setD2('');
    setLap1('');
    setLap2('');
    setLoadProgress('Starting session load…');

    try {
      // Step 1: Trigger background load
      const loadRes = await fetch('/api/load-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ year, gp }),
      });
      const loadData = await loadRes.json();

      // Step 2: Poll for completion if not immediately ready
      if (loadData.status !== 'ready') {
        setLoadProgress('Loading telemetry data from FastF1…');
        let ready = false;
        const startTime = Date.now();
        while (!ready) {
          await new Promise(r => setTimeout(r, 1000)); // poll every 1s
          const elapsed = Math.round((Date.now() - startTime) / 1000);
          setLoadProgress(`Loading telemetry data… ${elapsed}s`);

          const statusRes = await fetch(
            `/api/session-status?year=${year}&gp=${encodeURIComponent(gp)}`
          );
          const statusData = await statusRes.json();

          if (statusData.status === 'ready') {
            ready = true;
          } else if (statusData.status === 'error') {
            throw new Error(statusData.error || 'Failed to load session');
          }
          // timeout after 120s
          if (elapsed > 120) throw new Error('Session load timed out');
        }
      }

      // Step 3: Fetch drivers
      setLoadProgress('Processing driver data…');
      const driverRes = await fetch(
        `/api/drivers?year=${year}&gp=${encodeURIComponent(gp)}`
      );
      if (!driverRes.ok) throw new Error('Failed to load driver data');
      const driverData = await driverRes.json();

      setDrivers(driverData.drivers);
      setSessionLabel(`${year} ${gp} GP — Qualifying`);
      if (driverData.drivers.length >= 2) {
        setD1(driverData.drivers[0].driver);
        setD2(driverData.drivers[1].driver);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoadingDrivers(false);
      setLoadProgress('');
    }
  }, [year, gp]);

  const handleCompare = async () => {
    if (!d1 || !d2) return;
    setLoading(true);
    setError('');
    setComparison(null);
    setTrackData(null);

    const params = new URLSearchParams({
      d1, d2,
      year: String(year),
      gp,
    });
    if (lap1) params.append('lap1', lap1);
    if (lap2) params.append('lap2', lap2);

    try {
      const [compRes, trackRes] = await Promise.all([
        fetch(`/api/compare?${params}`),
        fetch(`/api/track-dominance?${params}`),
      ]);

      if (!compRes.ok) {
        const err = await compRes.json();
        throw new Error(err.error || 'Comparison failed');
      }

      const compData = await compRes.json();
      const trackDataJson = trackRes.ok ? await trackRes.json() : null;

      setComparison(compData);
      setTrackData(trackDataJson);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const getDriverInfo = (abbr) => drivers.find(d => d.driver === abbr);

  // Dynamic background gradient colors based on selected drivers
  const info1 = getDriverInfo(d1);
  const info2 = getDriverInfo(d2);
  const appStyle = comparison ? {
    '--color-d1': comparison.color1 || '#E10600',
    '--color-d2': comparison.color2 || '#00D2BE',
  } : {
    '--color-d1': info1?.color || '#E10600',
    '--color-d2': info2?.color || '#00D2BE',
  };

  return (
    <div className={`app ${comparison ? 'app--compared' : ''}`} style={appStyle}>
      <Navbar sessionLabel={sessionLabel} />

      <div className="app-container">
        {/* Session Selector */}
        <SessionSelector
          year={year}
          gp={gp}
          setYear={setYear}
          setGp={setGp}
          onSessionLoaded={loadDrivers}
        />

        {loadingDrivers && (
          <div className="loading-overlay">
            <div className="spinner" />
            <div className="loading-text">{loadProgress || 'Loading…'}</div>
          </div>
        )}

        {/* Driver Selectors — only show when drivers are loaded */}
        {drivers.length > 0 && (
          <>
            <DriverSelector
              drivers={drivers}
              d1={d1} d2={d2}
              setD1={setD1} setD2={setD2}
              lap1={lap1} lap2={lap2}
              setLap1={setLap1} setLap2={setLap2}
              getDriverInfo={getDriverInfo}
            />

            <button
              className="compare-btn"
              onClick={handleCompare}
              disabled={!d1 || !d2 || d1 === d2 || loading}
            >
              {loading ? 'Analysing…' : 'Compare Drivers'}
            </button>
          </>
        )}

        {error && (
          <div className="empty-state">
            <div className="empty-state__icon">⚠️</div>
            <div className="empty-state__msg">{error}</div>
          </div>
        )}

        {loading && (
          <div className="loading-overlay">
            <div className="spinner" />
            <div className="loading-text">Loading telemetry data…</div>
          </div>
        )}

        {comparison && !loading && (
          <>
            <VerdictBanner comparison={comparison} />

            <div className="section-header fade-in stagger-1">
              <div className="accent-line" />
              <h2>Sector Performance</h2>
            </div>
            <SectorCards comparison={comparison} />

            {trackData && (
              <>
                <div className="section-header fade-in stagger-3">
                  <div className="accent-line" />
                  <h2>Track Dominance</h2>
                </div>
                <TrackDominance data={trackData} />
              </>
            )}

            <div className="section-header fade-in stagger-4">
              <div className="accent-line" />
              <h2>Speed Traps</h2>
            </div>
            <SpeedTraps comparison={comparison} />
          </>
        )}

        {!comparison && !loading && !loadingDrivers && drivers.length === 0 && !error && (
          <div className="empty-state">
            <div className="empty-state__icon">🏁</div>
            <div className="empty-state__msg">
              Select a <strong>Season</strong> and <strong>Grand Prix</strong> above, then
              click <strong>Load Session</strong> to get started.
            </div>
          </div>
        )}

        {!comparison && !loading && !loadingDrivers && drivers.length > 0 && (
          <div className="empty-state">
            <div className="empty-state__icon">🏎️</div>
            <div className="empty-state__msg">
              Select two drivers and click <strong>Compare Drivers</strong> to
              see a full sector-by-sector analysis.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
