import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Camera, ShieldCheck, ShieldAlert, Users, Activity, Bell, Maximize2, Play, Square } from "lucide-react";
import "./styles.css";

const initialEvents = [
  { time: "17:08:42", type: "System", message: "Monitoring started", level: "normal" },
  { time: "17:08:55", type: "AI", message: "Person detected outside restricted zone", level: "normal" },
];

function App() {
  const videoRef = useRef(null);
  const [monitoring, setMonitoring] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [alert, setAlert] = useState(false);
  const [events, setEvents] = useState(initialEvents);

  useEffect(() => () => stopCamera(), []);

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      videoRef.current.srcObject = stream;
      setCameraReady(true);
      setMonitoring(true);
      addEvent("System", "Camera connected — monitoring active", "normal");
    } catch {
      addEvent("System", "Camera permission denied or unavailable", "danger");
    }
  }

  function stopCamera() {
    const stream = videoRef.current?.srcObject;
    stream?.getTracks().forEach((track) => track.stop());
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraReady(false);
    setMonitoring(false);
  }

  function addEvent(type, message, level) {
    const time = new Date().toLocaleTimeString("en-IN", { hour12: false });
    setEvents((current) => [{ time, type, message, level }, ...current].slice(0, 8));
  }

  function simulateIntrusion() {
    setAlert(true);
    addEvent("ALERT", "Unauthorized person entered kitchen zone", "danger");
    window.setTimeout(() => setAlert(false), 5000);
  }

  const status = alert ? "INTRUSION DETECTED" : monitoring ? "MONITORING ACTIVE" : "SYSTEM STANDBY";

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><ShieldCheck size={22} /></div>
          <div><strong>KitchenGuard</strong><span>AI SAFETY MONITOR</span></div>
        </div>
        <div className={`system-pill ${alert ? "danger" : monitoring ? "live" : ""}`}>
          <span className="dot" /> {status}
        </div>
      </header>

      {alert && (
        <div className="alert-banner">
          <ShieldAlert size={21} />
          <div><strong>INTRUSION ALERT</strong><span>Person detected inside the restricted kitchen zone.</span></div>
          <button onClick={() => setAlert(false)}>Dismiss</button>
        </div>
      )}

      <main className="dashboard">
        <section className="hero-row">
          <div>
            <p className="eyebrow">REAL-TIME COMPUTER VISION</p>
            <h1>Kitchen safety, <em>watched intelligently.</em></h1>
            <p className="subhead">Monitor a restricted kitchen zone with camera input, YOLO-based person detection and instant intrusion events.</p>
          </div>
          <div className="controls">
            {!monitoring ? (
              <button className="primary" onClick={startCamera}><Play size={17} /> Start camera</button>
            ) : (
              <button className="secondary" onClick={stopCamera}><Square size={15} /> Stop</button>
            )}
            <button className="demo" onClick={simulateIntrusion}><Bell size={16} /> Demo alert</button>
          </div>
        </section>

        <section className="grid">
          <div className="card camera-card">
            <div className="card-head"><div><span className="label">CAMERA 01</span><h2>Kitchen Zone</h2></div><span className="live-tag">● LIVE</span></div>
            <div className="video-wrap">
              <video ref={videoRef} autoPlay playsInline muted className={cameraReady ? "camera-video" : "camera-video hidden"} />
              {!cameraReady && <div className="camera-placeholder"><Camera size={42} /><strong>Camera feed offline</strong><span>Start the camera to preview the monitoring area.</span></div>}
              <div className={`zone-overlay ${alert ? "alert-zone" : ""}`}><span>RESTRICTED ZONE</span></div>
              {alert && <div className="intrusion-overlay"><ShieldAlert size={30} /><strong>INTRUSION DETECTED</strong><span>Person inside restricted zone</span></div>}
              <button className="fullscreen" title="Fullscreen"><Maximize2 size={16} /></button>
            </div>
            <div className="camera-foot"><span><Activity size={15} /> YOLO object detection</span><span>OpenCV processing</span></div>
          </div>

          <aside className="side-stack">
            <div className={`card status-card ${alert ? "danger-card" : ""}`}>
              <div className="stat-icon">{alert ? <ShieldAlert /> : <ShieldCheck />}</div>
              <div><span className="label">SAFETY STATUS</span><h2>{alert ? "Attention required" : monitoring ? "Area secure" : "Ready"}</h2><p>{alert ? "Immediate review recommended" : "No active intrusion"}</p></div>
            </div>
            <div className="metrics">
              <div className="metric card"><Users size={19} /><span>PERSONS</span><strong>{alert ? 1 : 0}</strong></div>
              <div className="metric card"><Activity size={19} /><span>DETECTION</span><strong>{monitoring ? "ON" : "OFF"}</strong></div>
            </div>
            <div className="card zone-card"><div className="card-head"><div><span className="label">ZONE CONFIGURATION</span><h2>Kitchen</h2></div><span className="zone-state">RESTRICTED</span></div><div className="zone-line"><span />Detection zone armed</div><p>Intrusion is triggered when a detected person's center point enters the configured zone.</p></div>
          </aside>
        </section>

        <section className="card events-card">
          <div className="card-head"><div><span className="label">EVENT MONITOR</span><h2>Recent events</h2></div><span className="event-count">{events.length} events</span></div>
          <div className="events-list">{events.map((event, index) => <div className="event" key={`${event.time}-${index}`}><span className="event-time">{event.time}</span><span className={`event-badge ${event.level}`}>{event.type}</span><span>{event.message}</span></div>)}</div>
        </section>

        <footer><span>KitchenGuard Prototype</span><span>AI detection • Zone monitoring • Event alerts</span></footer>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
