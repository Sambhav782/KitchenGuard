import { useEffect, useRef, useState } from "react";

function App() {
  const [events, setEvents] = useState([]);
  const [points, setPoints] = useState([]);
  const [source, setSource] = useState("demo");

  const feedRef = useRef(null);

  // ============================================================
  // LOAD EXISTING EVENTS
  // ============================================================

  useEffect(() => {
    fetch("http://localhost:5000/api/events")
      .then((response) => response.json())
      .then((data) => {
        setEvents(data);
      })
      .catch((error) => {
        console.error("Error fetching events:", error);
      });
  }, []);

  // ============================================================
  // LIVE INTRUSION EVENTS
  // ============================================================

  useEffect(() => {
    const eventSource = new EventSource("http://localhost:5001/events/stream");

    eventSource.onmessage = (event) => {
      try {
        const newEvent = JSON.parse(event.data);

        setEvents((prevEvents) => [newEvent, ...prevEvents]);
      } catch (error) {
        console.error("Error processing intrusion event:", error);
      }
    };

    eventSource.onerror = (error) => {
      console.error("Intrusion event connection error:", error);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  // ============================================================
  // CONFIRM RESTRICTED ZONE
  // ============================================================

  const confirmZone = () => {
    if (points.length < 3) {
      return;
    }

    fetch("http://localhost:5001/zone", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        points: points,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Zone sent:", data);
      })
      .catch((error) => {
        console.error("Error sending zone:", error);
      });
  };

  // ============================================================
  // CHANGE VIDEO SOURCE
  // ============================================================

  const changeSource = (newSource) => {
    // ----------------------------------------------------------
    // Clear the old restricted zone immediately.
    // Each source needs its own zone.
    // ----------------------------------------------------------

    setPoints([]);

    // ----------------------------------------------------------
    // Change the UI source
    // ----------------------------------------------------------

    setSource(newSource);

    // ----------------------------------------------------------
    // Tell Python to change the actual source
    // ----------------------------------------------------------

    fetch("http://localhost:5001/source", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        source: newSource,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Source changed:", data);
      })
      .catch((error) => {
        console.error("Error changing source:", error);
      });
  };

  // ============================================================
  // CLEAR SELECTED POINTS
  // ============================================================

  const clearPoints = () => {
    setPoints([]);
  };

  return (
    <div className="app">
      {/* ======================================================
      TOP BAR
  ====================================================== */}

      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">T</div>

          <div>
            <h1>TRINETRA</h1>

            <p>Threat Recognition & Intelligent Network</p>
          </div>
        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          SYSTEM ONLINE
        </div>
      </header>

      {/* ======================================================
      DASHBOARD
  ====================================================== */}

      <main className="dashboard">
        {/* PAGE HEADER */}

        <section className="page-header">
          <div>
            <div className="eyebrow">SECURITY MONITORING</div>

            <h2>Border Surveillance</h2>

            <p>Real-time monitoring and intelligent intrusion detection</p>
          </div>

          <div className="monitor-status">
            <span className="monitor-dot"></span>
            MONITORING ACTIVE
          </div>
        </section>

        {/* ====================================================
        MAIN GRID
    ==================================================== */}

        <section className="dashboard-grid">
          {/* ==================================================
          SURVEILLANCE CARD
      ================================================== */}

          <div className="card surveillance-card">
            <div className="card-header">
              <div>
                <span className="card-label">PRIMARY FEED</span>

                <h3>Surveillance Feed</h3>
              </div>

              {/* SOURCE TOGGLE */}

              <div className="source-toggle">
                <button
                  className={
                    source === "live" ? "source-button active" : "source-button"
                  }
                  onClick={() => changeSource("live")}
                >
                  LIVE CAMERA
                </button>

                <button
                  className={
                    source === "demo" ? "source-button active" : "source-button"
                  }
                  onClick={() => changeSource("demo")}
                >
                  DEMO VIDEO
                </button>
              </div>
            </div>

            {/* =================================================
            VIDEO AREA
        ================================================= */}

            <div
              ref={feedRef}
              className="feed-container"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();

                const x = (e.clientX - rect.left) / rect.width;

                const y = (e.clientY - rect.top) / rect.height;

                setPoints((prev) => [...prev, [x, y]]);
              }}
            >
              {/* =================================================
              SURVEILLANCE FEED
          ================================================= */}

              <img
                key={source}
                src={`http://localhost:5001/video?source=${source}`}
                alt="Surveillance Feed"
                className="surveillance-image feed-visible"
              />

              {/* =================================================
              ZONE OVERLAY
          ================================================= */}

              <svg
                className="zone-overlay"
                viewBox="0 0 1 1"
                preserveAspectRatio="none"
              >
                {points.length > 0 && (
                  <polygon
                    points={points.map(([x, y]) => `${x},${y}`).join(" ")}
                    fill="rgba(255, 70, 70, 0.12)"
                    stroke="#ff5c5c"
                    strokeWidth="0.004"
                  />
                )}

                {points.map(([x, y], index) => (
                  <circle key={index} cx={x} cy={y} r="0.006" fill="#ff5c5c" />
                ))}
              </svg>

              {/* =================================================
              CORNERS
          ================================================= */}

              <div className="corner corner-tl"></div>

              <div className="corner corner-tr"></div>

              <div className="corner corner-bl"></div>

              <div className="corner corner-br"></div>

              {/* =================================================
              FEED LABEL
          ================================================= */}

              <div className="feed-overlay">
                <span>CAM-01</span>

                <span>● ACTIVE</span>
              </div>
            </div>

            {/* =================================================
            ZONE CONTROLS
        ================================================= */}

            <div className="zone-controls">
              <div className="zone-info">
                <div className="zone-icon">⌖</div>

                <div>
                  <strong>Restricted Zone</strong>

                  <span>
                    {points.length === 0
                      ? "Click the feed to define an area"
                      : `${points.length} points selected`}
                  </span>
                </div>
              </div>

              {/* =================================================
              ZONE ACTIONS
          ================================================= */}

              <div className="zone-actions">
                <button
                  className="clear-button"
                  onClick={clearPoints}
                  disabled={points.length === 0}
                >
                  Clear Points
                </button>

                <button
                  className="confirm-button"
                  onClick={confirmZone}
                  disabled={points.length < 3}
                >
                  Confirm Zone
                </button>
              </div>
            </div>
          </div>

          {/* ==================================================
          INTRUSION PANEL
      ================================================== */}

          <div className="card intrusion-card">
            <div className="card-header">
              <div>
                <span className="card-label">SECURITY EVENTS</span>

                <h3>Recent Intrusions</h3>
              </div>

              <div className="event-count">{events.length}</div>
            </div>

            {/* =================================================
            EVENTS LIST
        ================================================= */}

            <div className="events-list">
              {events.length === 0 ? (
                <div className="empty-events">
                  <div className="empty-icon">✓</div>

                  <strong>No Intrusions Detected</strong>

                  <span>The monitored area is currently secure.</span>
                </div>
              ) : (
                events.map((event, index) => (
                  <div
                    className="event"
                    key={`${event.personId}-${event.time}-${index}`}
                  >
                    <div className="event-image-wrapper">
                      <img
                        src={`http://localhost:5000/${event.snapshot}`}
                        alt={`Intrusion by Person ${event.personId}`}
                        className="event-snapshot"
                      />

                      <span className="event-alert-dot"></span>
                    </div>

                    <div className="event-info">
                      <strong>INTRUSION DETECTED</strong>

                      <span>
                        PERSON ID&nbsp;&nbsp;
                        <b>#{event.personId}</b>
                      </span>

                      <span>{event.time}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </main>

      {/* ======================================================
      FOOTER
  ====================================================== */}

      <footer className="dashboard-footer">
        <span>TRINETRA SECURITY SYSTEM</span>

        <span>AI-POWERED BORDER MONITORING</span>

        <span>v1.0</span>
      </footer>
    </div>
  );
}

export default App;
