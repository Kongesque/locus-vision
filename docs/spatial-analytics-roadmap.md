# LocusVision Spatial Analytics Platform - Roadmap

## Positioning Statement

**LocusVision is a spatial analytics platform** that uses computer vision to transform video feeds into structured data, insights, and actionable intelligence.

- **Primary**: Spatial analytics, people counting, zone-based tracking
- **Secondary**: NVR capabilities (recording, alerts)
- **Differentiator**: Data export, reporting, business intelligence integration

---

## 🎯 Core Value Proposition

> "Turn any camera into a data source. Understand how people move through spaces."

### Use Cases
| Industry | Application |
|----------|-------------|
| **Retail** | Customer flow analysis, heatmaps, dwell time, conversion rates |
| **Smart Buildings** | Occupancy monitoring, space utilization, energy optimization |
| **Transportation** | Passenger counting, queue management, crowd density |
| **Manufacturing** | Workflow optimization, safety compliance, productivity metrics |
| **Events** | Attendance tracking, crowd flow, security zone monitoring |
| **Urban Planning** | Pedestrian patterns, traffic analysis, public space usage |

---

## 🗺️ Roadmap Phases

> **Legend**: 
> ⭐ = MVP Priority (Required for Beta)
> 🔥 = WOW Factor (High visual impact for Showcases)

### Phase 1: Core Spatial Analytics Engine (Current - Month 1-2)

#### ✅ Completed
- [x] Zone-based polygon counting ⭐
- [x] Line crossing detection (bidirectional) ⭐
- [x] ByteTrack multi-object tracking ⭐
- [x] Class filtering (person, car, etc.) ⭐
- [x] Real-time live stream processing 🔥
- [x] Basic metrics collection (Frigate-style) ⭐

#### 🚧 In Progress / Needed

**1.1 Enhanced Zone Analytics**
```
- [x] Zone dwell time (how long objects stay in zone) ⭐
- [x] Zone entry/exit timestamps ⭐
- [ ] Zone occupancy (current count in zone) - Frontend tracking needed ⭐
- [x] Zone capacity alerts (80% full, etc.) ⭐
- [ ] Zone groups (combine multiple zones)
- [ ] Nested zones (zone within zone)
```

**1.2 Line Analytics**
```
- [x] Multi-line support with naming ⭐
- [ ] Line crossing velocity (speed estimation)
- [x] Line crossing direction heatmap (Data tracked, UI needed) 🔥
- [ ] Peak crossing times
- [ ] Time-between-crossings (flow rate)
```

**1.3 Object Tracking & Behavior**
```
- [x] Object trajectory recording (path history - tracked in DuckDB) 🔥
- [ ] Average speed per zone
- [x] Direction of movement (N/E/S/W - anomaly tracking implemented) ⭐
- [x] Object classification persistence (track "person" across zones) ⭐
- [ ] Group detection (people moving together) 🔥
```

---

### Phase 2: Data & Analytics Platform (Month 2-3)

#### 2.1 Data Export & APIs
```
- [x] REST API for all analytics data ⭐
- [ ] Real-time data streaming (WebSocket/SSE) 🔥
- [x] CSV export (hourly/daily/weekly aggregates) ⭐
- [x] JSON API for integrations ⭐
- [ ] Webhook callbacks on events
- [ ] MQTT publisher for IoT integration
```

#### 2.2 Time-Series Database
```
- [x] DuckDB integration (Replaced InfluxDB/TimescaleDB) ⭐
- [x] Store: counts, dwell times, flow rates per zone ⭐
- [x] Retention policies (raw 7d, hourly 90d, daily 1y) ⭐
- [x] Downsampling for long-term storage ⭐
```

#### 2.3 Reporting Engine
```
- [ ] Daily/weekly/monthly PDF reports
- [ ] Custom date range reports
- [ ] Report templates by industry
  - Retail: Traffic, conversion, heatmap
  - Buildings: Occupancy, peak hours
  - Transport: Passenger flow, queue times
- [ ] Automated email reports
- [ ] Report scheduling (daily at 9am)
```

#### 2.4 Visualizations
```
- [x] Heatmap overlay on camera view 🔥
- [ ] Flow diagrams (Sankey diagrams for zone transitions) 🔥
- [ ] Time-series charts (counts over time) ⭐
- [ ] Comparison charts (Zone A vs Zone B)
- [ ] Peak hours identification ⭐
- [ ] Trend analysis (week-over-week, month-over-month)
```

---

### Phase 3: Advanced Analytics (Month 3-4)

#### 3.1 Behavioral Analytics
```
- [ ] Path analysis (common routes through space) 🔥
- [ ] Stop detection (loitering identification)
- [ ] Queue analysis (length, wait time, service time)
- [ ] Social distancing compliance (if applicable)
- [ ] Anomaly detection (unusual patterns) 🔥
- [ ] Predictive analytics (forecast next hour traffic)
```

#### 3.2 Multi-Camera & Multi-Location
```
- [ ] Camera groups (floor, building, region)
- [ ] Cross-camera tracking (same person, different cameras)
- [ ] Multi-location dashboard
- [ ] Location comparison (Store A vs Store B)
- [ ] Aggregate analytics across locations
```

#### 3.3 Business Intelligence Integrations
```
- [ ] Grafana plugin/datasource
- [ ] Power BI connector
- [ ] Tableau integration
- [ ] Google Data Studio
- [ ] Excel/Google Sheets live data
- [ ] Custom dashboard builder (drag-drop widgets)
```

---

### Phase 4: NVR Foundation (Month 4-5)

*Lightweight NVR capabilities to support analytics*

#### 4.1 Recording (Analytics-First)
```
- [ ] Motion-triggered recording (not continuous)
- [ ] Event-based clips (±30 seconds around detection)
- [ ] Search by: date, zone, object type, direction
- [ ] Thumbnail previews
- [ ] Export clip to MP4
- [ ] Circular buffer (auto-delete after N days)
```

#### 4.2 Alerting (Analytics-Driven)
```
- [ ] Zone capacity alerts (>80% occupancy)
- [ ] Dwell time alerts (loitering detection)
- [ ] Flow rate alerts (sudden crowd surge)
- [ ] Direction alerts (wrong-way detection)
- [ ] Webhook/API callbacks (not just email)
- [ ] Alert rules engine (IF zone A count > 10 AND time > 18:00)
```

#### 4.3 Live View (Analytics Overlay)
```
- [ ] Multi-camera grid (2x2, 3x3) ⭐
- [ ] Real-time zone counts overlay ⭐
- [ ] Live heatmap overlay 🔥
- [ ] Current occupancy display ⭐
- [ ] Mini dashboard per camera
```

---

### Phase 5: Scale & Enterprise (Month 5-6)

#### 5.1 Multi-Node Architecture
```
- [ ] Edge nodes (RPi5 + Hailo at each location)
- [ ] Central aggregation server
- [ ] Distributed processing
- [ ] Cloud relay for remote management
- [ ] Edge-cloud sync
```

#### 5.2 Enterprise Features
```
- [ ] SSO/SAML integration
- [ ] Role-based access control (RBAC)
- [ ] Audit logging (who viewed what when)
- [ ] API rate limiting
- [ ] White-label option
- [ ] Multi-tenant support
```

#### 5.3 Advanced Integrations
```
- [ ] POS integration (correlate foot traffic with sales)
- [ ] Access control systems (badge + video correlation)
- [ ] HVAC integration (occupancy-based climate control)
- [ ] Digital signage (adapt content to crowd size)
- [ ] Slack/Teams notifications
```

---

## 🏗️ Technical Architecture Evolution

### Current (Phase 1)
```
┌─────────────────────────────────────┐
│  SvelteKit Frontend                 │
├─────────────────────────────────────┤
│  FastAPI Backend                    │
│  - SQLite (config, events)          │
│  - In-memory metrics                │
├─────────────────────────────────────┤
│  ONNX Runtime (CPU)                 │
│  - YOLO11n detection                │
│  - ByteTrack tracking               │
│  - Zone/line analytics              │
└─────────────────────────────────────┘
```

### Phase 2-3 (Analytics Platform)
```
┌─────────────────────────────────────┐
│  SvelteKit Frontend                 │
│  - Dashboard builder                │
│  - Report viewer                    │
│  - Data export UI                   │
├─────────────────────────────────────┤
│  FastAPI Backend                    │
│  - SQLite (config, users)           │
│  - TimescaleDB (time-series data)   │
│  - Report generation                │
│  - API gateway                      │
├─────────────────────────────────────┤
│  Analytics Engine                   │
│  - Zone/line analytics              │
│  - Behavior analysis                │
│  - Data aggregation                 │
├─────────────────────────────────────┤
│  Inference (ONNX/Hailo)             │
└─────────────────────────────────────┘
```

### Phase 4-5 (Distributed)
```
┌─────────────────────────────────────┐
│  Central Dashboard                  │
├─────────────────────────────────────┤
│  Aggregation API                    │
│  - Multi-location data              │
│  - Central reporting                │
├─────────────────────────────────────┤
│  Edge Node 1        Edge Node 2     │
│  - Local processing  - Local proc   │
│  - Local storage     - Local store  │
│  - Sync to central   - Sync to cen  │
└─────────────────────────────────────┘
```

---

## 📊 Key Metrics to Track

### Platform Health
- Detection latency (p50, p90, p99)
- Tracking accuracy (ID switches)
- System CPU/memory
- Camera stream health

### Analytics Quality
- False positive rate
- Missed detection rate
- Zone accuracy
- Count accuracy vs ground truth

### Business Value
- Data export frequency
- API call volume
- Report generation count
- User engagement (daily active)

---

## 🎨 UI/UX Priorities

### Analytics Dashboard
```
┌─────────────────────────────────────────────┐
│  Date Range Selector    [Export] [Report]   │
├─────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Visitors │ │ Dwell    │ │ Peak     │    │
│  │ Today    │ │ Avg      │ │ Hour     │    │
│  │ 1,247    │ │ 4m 32s   │ │ 2:00 PM  │    │
│  └──────────┘ └──────────┘ └──────────┘    │
├─────────────────────────────────────────────┤
│  [Time Series Chart: Visitors per Hour]     │
├─────────────────────────────────────────────┤
│  [Heatmap Overlay on Floor Plan]            │
├─────────────────────────────────────────────┤
│  [Flow Diagram: Zone A → Zone B → Zone C]   │
└─────────────────────────────────────────────┘
```

### Zone Configuration
```
┌─────────────────────────────────────────────┐
│  Camera Feed                                │
│  ┌─────────┐                                │
│  │ Zone A  │  ← Drag to draw zones         │
│  │ [Count] │                                │
│  └─────────┘                                │
│       ↓                                     │
│  ┌─────────┐                                │
│  │ Zone B  │  ← Visual flow arrows         │
│  └─────────┘                                │
├─────────────────────────────────────────────┤
│  Zone A Settings:                           │
│  - Name: "Entrance"                         │
│  - Type: Entry/Exit/Dwell                   │
│  - Alert: >50 people                        │
└─────────────────────────────────────────────┘
```

---

## 🛣️ Immediate Next Steps (This Week)

### ✅ 1. Dwell Time Tracking
Add to `AnalyticsEngine`:
```python
# Track how long each object stays in a zone
zone_entry_times: Dict[str, Dict[int, float]]  # zone_id -> {track_id: timestamp}
dwell_times: List[float]  # rolling window of dwell times
```

### ✅ 2. Time-Series Data Export
Create export endpoint:
```python
GET /api/analytics/export?zone=entrance&start=2024-01-01&end=2024-01-31&format=csv

Returns:
timestamp,zone_id,enter_count,exit_count,avg_dwell_sec
2024-01-01T09:00:00,entrance,45,12,180
...
```

### ✅ 3. Heatmap Generation
```python
# Accumulate detection centers over time
create_heatmap(camera_id, duration_minutes=60) -> PNG overlay
```

### 4. Zone Grouping
```
Floor 1 (Group)
├── Entrance (Zone)
├── Checkout (Zone)
└── Exit (Zone)
```

---

## 💰 Monetization Potential (Future)

### Open Source Core
- Zone-based counting
- Line crossing
- Basic reporting
- Single camera

### Commercial Add-ons
- Multi-location aggregation
- Advanced analytics (heatmaps, predictions)
- White-label
- Enterprise SSO
- Custom model training
- Cloud hosting

### Target Customers
- **Retail chains**: $200-500/month per location
- **Smart building operators**: $1000-3000/month building
- **Event venues**: $500-1500/event
- **City governments**: Custom contracts

---

## 🎯 Success Metrics (6 Months)

- [ ] 10+ beta deployments (retail, buildings, events)
- [ ] 90%+ counting accuracy vs manual
- [ ] <100ms detection latency with Hailo
- [ ] 50+ API integrations
- [ ] Export 1M+ analytics events/day across all deployments

---

## Summary

**LocusVision is not an NVR with analytics—it's an analytics platform that can record video.**

Focus on:
1. **Data quality** (accurate counts, low latency)
2. **Data export** (APIs, integrations, BI tools)
3. **Insights** (reports, visualizations, predictions)
4. **Scale** (multi-location, enterprise)

NVR features support the analytics but aren't the product.
