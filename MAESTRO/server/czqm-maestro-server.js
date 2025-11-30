/**
 * CZQM MAESTRO Server
 * Handles multi-user synchronization of arrival sequence data
 * 
 * Features:
 * - Master/Slave controller coordination
 * - Persistent sequence storage
 * - Real-time data sharing between controllers
 * - Support for CYQX, CYHZ, CYYT
 */

const express = require('express');
const app = express();
const port = 3000;

app.use(express.json());

// In-memory storage for sequence data
// In production, replace with Redis or database
const sequenceData = {
  CYQX: { master: null, sequence: [], lastUpdate: null },
  CYHZ: { master: null, sequence: [], lastUpdate: null },
  CYYT: { master: null, sequence: [], lastUpdate: null }
};

// CORS middleware for EuroScope plugin access
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
  next();
});

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

/**
 * Register as MASTER for an airport
 * POST /api/maestro/:airport/master
 * Body: { controllerId: "CZQX_APP", frequency: "127.700" }
 */
app.post('/api/maestro/:airport/master', (req, res) => {
  const airport = req.params.airport.toUpperCase();
  const { controllerId, frequency } = req.body;

  if (!sequenceData[airport]) {
    return res.status(400).json({ error: 'Invalid airport' });
  }

  // Check if another master is already active
  if (sequenceData[airport].master && 
      sequenceData[airport].master.controllerId !== controllerId) {
    return res.status(409).json({ 
      error: 'Another MASTER is already active',
      currentMaster: sequenceData[airport].master 
    });
  }

  sequenceData[airport].master = {
    controllerId,
    frequency,
    connectedAt: new Date().toISOString(),
    lastHeartbeat: new Date().toISOString()
  };

  console.log(`[${airport}] MASTER registered: ${controllerId}`);
  
  res.json({ 
    success: true, 
    airport,
    master: sequenceData[airport].master,
    currentSequence: sequenceData[airport].sequence
  });
});

/**
 * Update sequence data (MASTER only)
 * PUT /api/maestro/:airport/sequence
 * Body: { controllerId: "CZQX_APP", sequence: [...] }
 */
app.put('/api/maestro/:airport/sequence', (req, res) => {
  const airport = req.params.airport.toUpperCase();
  const { controllerId, sequence } = req.body;

  if (!sequenceData[airport]) {
    return res.status(400).json({ error: 'Invalid airport' });
  }

  // Verify caller is the MASTER
  if (!sequenceData[airport].master || 
      sequenceData[airport].master.controllerId !== controllerId) {
    return res.status(403).json({ error: 'Only MASTER can update sequence' });
  }

  sequenceData[airport].sequence = sequence;
  sequenceData[airport].lastUpdate = new Date().toISOString();
  sequenceData[airport].master.lastHeartbeat = new Date().toISOString();

  console.log(`[${airport}] Sequence updated: ${sequence.length} aircraft`);

  res.json({ success: true, sequenceCount: sequence.length });
});

/**
 * Get sequence data (SLAVE controllers)
 * GET /api/maestro/:airport/sequence
 */
app.get('/api/maestro/:airport/sequence', (req, res) => {
  const airport = req.params.airport.toUpperCase();

  if (!sequenceData[airport]) {
    return res.status(400).json({ error: 'Invalid airport' });
  }

  res.json({
    airport,
    master: sequenceData[airport].master,
    sequence: sequenceData[airport].sequence,
    lastUpdate: sequenceData[airport].lastUpdate
  });
});

/**
 * Heartbeat endpoint for MASTER
 * POST /api/maestro/:airport/heartbeat
 */
app.post('/api/maestro/:airport/heartbeat', (req, res) => {
  const airport = req.params.airport.toUpperCase();
  const { controllerId } = req.body;

  if (!sequenceData[airport] || !sequenceData[airport].master) {
    return res.status(404).json({ error: 'No MASTER registered' });
  }

  if (sequenceData[airport].master.controllerId !== controllerId) {
    return res.status(403).json({ error: 'Not the active MASTER' });
  }

  sequenceData[airport].master.lastHeartbeat = new Date().toISOString();
  res.json({ success: true });
});

/**
 * Release MASTER status
 * DELETE /api/maestro/:airport/master
 */
app.delete('/api/maestro/:airport/master', (req, res) => {
  const airport = req.params.airport.toUpperCase();
  const { controllerId } = req.body;

  if (!sequenceData[airport]) {
    return res.status(400).json({ error: 'Invalid airport' });
  }

  if (sequenceData[airport].master && 
      sequenceData[airport].master.controllerId === controllerId) {
    console.log(`[${airport}] MASTER released: ${controllerId}`);
    sequenceData[airport].master = null;
    res.json({ success: true });
  } else {
    res.status(403).json({ error: 'Not the active MASTER' });
  }
});

/**
 * Get system status
 * GET /api/maestro/status
 */
app.get('/api/maestro/status', (req, res) => {
  const status = {};
  
  Object.keys(sequenceData).forEach(airport => {
    status[airport] = {
      hasMaster: !!sequenceData[airport].master,
      master: sequenceData[airport].master?.controllerId,
      aircraftCount: sequenceData[airport].sequence.length,
      lastUpdate: sequenceData[airport].lastUpdate
    };
  });

  res.json(status);
});

/**
 * Auto-cleanup stale MASTER connections
 * Runs every 60 seconds
 */
setInterval(() => {
  const now = new Date();
  const timeout = 120000; // 2 minutes

  Object.keys(sequenceData).forEach(airport => {
    if (sequenceData[airport].master) {
      const lastHeartbeat = new Date(sequenceData[airport].master.lastHeartbeat);
      const elapsed = now - lastHeartbeat;

      if (elapsed > timeout) {
        console.log(`[${airport}] MASTER timeout, releasing: ${sequenceData[airport].master.controllerId}`);
        sequenceData[airport].master = null;
      }
    }
  });
}, 60000);

// Start server
app.listen(port, () => {
  console.log(`CZQM MAESTRO Server running on port ${port}`);
  console.log(`Airports configured: ${Object.keys(sequenceData).join(', ')}`);
  console.log('\nEndpoints:');
  console.log(`  GET  /health`);
  console.log(`  GET  /api/maestro/status`);
  console.log(`  POST /api/maestro/:airport/master`);
  console.log(`  PUT  /api/maestro/:airport/sequence`);
  console.log(`  GET  /api/maestro/:airport/sequence`);
  console.log(`  POST /api/maestro/:airport/heartbeat`);
  console.log(`  DELETE /api/maestro/:airport/master`);
});

module.exports = app;
