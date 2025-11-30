# CZQM MAESTRO Quick Reference Card

## Connection Quick Start

### As MASTER (Approach/Planner)
1. Load MAESTRO.dll plugin
2. Click "Connect as MASTER (Web+Local)"
3. Select airport (CYHZ/CYYT/CYQX)
4. Set runway + arrival rate
5. ✅ You can now manage sequence

### As SLAVE (ACC/Tower)
1. Load MAESTRO.dll plugin
2. Click "Connect as SLAVE (Web+Local)"
3. Select same airport as MASTER
4. ✅ View sequence (read-only)

---

## Display Legend

### Aircraft States (Colors)
| Color | State | Meaning |
|-------|-------|---------|
| 🔴 Red | UNSTABLE | >12min from FF - sequence may change |
| 🟡 Yellow | STABLE | 8-12min from FF - limited changes |
| 🟢 Green | SUPER STABLE | 5-8min from FF - locked |
| ⚫ Black | FROZEN | <5min - no changes |

### Label Indicators
- **L03** = Lose 3 minutes (delay required)
- **G02** = Gain 2 minutes (speed up)
- **Seq:5** = 5th aircraft in sequence
- **●** = At feeder fix
- **○** = At runway threshold

---

## MASTER Quick Actions

### Basic Operations
| Action | How To |
|--------|--------|
| Set runway | Click runway selector |
| Set arrival rate | Click "Rate" → 20/25/30/35 |
| Insert slot | Right-click timeline → Insert Slot |
| Move aircraft | Drag on timeline OR click → Move Up/Down |
| Remove from seq | Right-click → De-sequence |

### Target Arrival Rates
- **Light traffic**: 20-25/hour
- **Moderate**: 25-30/hour  
- **Heavy/CTP**: 30/hour (max)
- **Consider**: Wake turbulence, controller experience

---

## Coordination Phraseology

### MASTER to SLAVE (ACC)
```
"Moncton Center, Halifax Approach,
ACA123 requires 3 minutes delay,
can you absorb in your airspace?"
```

### SLAVE Acknowledges
```
"Roger Halifax, will vector ACA123
for 3 minutes delay"
```

### ACC to APP Handoff
```
"ACA123, contact Halifax 119.2,
number 2 in sequence, 3 minutes
delay absorbed"
```

### APP to Tower
```
"Tower, Approach, ACA123 is
number 3, spacing is good,
clear to land when ready"
```

---

## Common Problems & Solutions

| Problem | Solution |
|---------|----------|
| Can't connect as MASTER | Someone else is MASTER - coordinate or connect as SLAVE |
| Sequence keeps changing | Normal if >12min from FF - wait until STABLE |
| No delays showing | Check MASTER is active and server connected |
| Aircraft missing | Verify flight plan has STAR, check route |
| Server timeout | Reconnect - sequence persists on server |

---

## Wake Turbulence Spacing

**Minimum Spacing (nautical miles):**

| Following | Behind Heavy | Behind Medium | Behind Light |
|-----------|--------------|---------------|--------------|
| Heavy | 4 NM | 3 NM | 3 NM |
| Medium | 5 NM | 3 NM | 3 NM |
| Light | 6 NM | 5 NM | 3 NM |

**MAESTRO Tip:** Insert 2-minute slot after heavy if light aircraft follows

---

## Emergency Procedures

### Server Down
1. Continue with last known sequence
2. Manual spacing (5-7 NM)
3. Voice coordination
4. Note sequence on scratch pad

### MASTER Disconnect
1. New MASTER connects as SLAVE first
2. Verify sees current sequence
3. Old MASTER disconnects
4. New MASTER reconnects as MASTER

### High Workload - Simplified Mode
1. Turn off auto-sequencing
2. Use fixed intervals (4-5 minutes)
3. Manual coordination only
4. Resume MAESTRO when stable

---

## When to Use Holding

MAESTRO calculates delays - but when delays exceed:
- **>10 minutes**: Consider holding
- **>15 minutes**: Definitely use holding
- Insert hold into sequence as slot

---

## Airports Configured

| Airport | Runways | Typical Rate | MASTER Position |
|---------|---------|--------------|-----------------|
| CYHZ | 05/23, 14/32 | 25-30/hr | YHZ_APP |
| CYYT | 11/29, 16/34 | 20-25/hr | YYT_APP |
| CYQX | 04/22, 13/31 | 25-30/hr | YQX_APP or CZQX_CTR |

---

## Support Contacts

- **Technical Issues**: [Discord #maestro-support]
- **Training**: training@czqm.ca
- **Operations**: ops@czqm.ca
- **Server Status**: http://maestro.czqm.ca/health

---

**Print this card and keep at your controlling position!**

*Version 1.0 - November 2025*
