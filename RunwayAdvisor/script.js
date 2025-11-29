// METAR Runway Advisor - Card-based version
// Shows ALL runways with visual wind components

const mainAirports = ["CYHZ", "CYYT", "CYFC", "CYQM", "CYSJ", "CYQX", "CYZX", "CYYG", "CYYR"];
const secondaryAirports = ["CYQI", "CYAY", "CYDF", "CYJT", "LFVP"];
const magneticVariation = 18; // West variation (Add to True Wind)

const runways = {
    CYHZ: { "05": 53, "32": 323, "23": 233, "14": 143 },
    CYYT: { "28": 283, "10": 103, "16": 156, "34": 336 },
    CYFC: { "09": 87, "15": 148, "27": 268, "33": 328 },
    CYQM: { "06": 61, "29": 286, "11": 106, "24": 241 },
    CYSJ: { "23": 229, "05": 49, "14": 138, "32": 319 },
    CYZX: { "08": 80, "12": 122, "26": 261, "30": 303 },
    CYYG: { "03": 27, "21": 207, "10": 97, "28": 277 },
    CYQX: { "21": 210, "03": 30, "13": 128, "31": 308 },
    CYYR: { "15": 153, "33": 333, "08": 75, "26": 255 },
    LFVP: { "08": 76, "26": 256 },
    CYQI: { "06": 59, "15": 150, "24": 239, "33": 330 },
    CYAY: { "10": 99, "28": 279 },
    CYDF: { "25": 244, "07": 64 },
    CYJT: { "27": 270, "09": 90 }
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    fetchAndDisplayData();
    
    // Auto-refresh every 15 minutes
    setInterval(fetchAndDisplayData, 15 * 60 * 1000);
    
    // Ad-hoc METAR request
    setupAdhocMetar();
});

document.getElementById('refresh-btn').addEventListener('click', () => {
    const btn = document.getElementById('refresh-btn');
    btn.classList.add('loading');
    fetchAndDisplayData().finally(() => {
        btn.classList.remove('loading');
    });
});

// Ad-hoc METAR setup
function setupAdhocMetar() {
    const input = document.getElementById('adhoc-icao');
    const button = document.getElementById('adhoc-fetch');
    
    button.addEventListener('click', () => fetchAdhocMetar());
    
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            fetchAdhocMetar();
        }
    });
    
    // Auto-uppercase input
    input.addEventListener('input', (e) => {
        e.target.value = e.target.value.toUpperCase();
    });
}

async function fetchAdhocMetar() {
    const input = document.getElementById('adhoc-icao');
    const button = document.getElementById('adhoc-fetch');
    const resultDiv = document.getElementById('adhoc-result');
    const icao = input.value.trim().toUpperCase();
    
    if (!icao || icao.length !== 4) {
        resultDiv.innerHTML = '<div class="error-card">Please enter a valid 4-letter ICAO code</div>';
        return;
    }
    
    button.disabled = true;
    button.textContent = 'Loading...';
    resultDiv.innerHTML = '<div style="color: #5dade2; padding: 20px; text-align: center;">Fetching data...</div>';
    
    try {
        const url = `https://avwx.rest/api/metar/${icao}?token=vmtkb1D8Tuva2Jw2tXihWcKE3m2sfDJkySBZygVx82I`;
        const response = await fetch(url);
        
        if (!response.ok) throw new Error(`Failed to fetch METAR for ${icao}`);
        
        const data = await response.json();
        const metar = data.raw || 'No METAR available';
        
        // Display just the raw METAR
        resultDiv.innerHTML = `
            <div class="adhoc-metar-display">
                <div class="adhoc-metar-header">${icao} METAR</div>
                <div class="adhoc-metar-text">${metar}</div>
            </div>
        `;
    } catch (error) {
        resultDiv.innerHTML = `<div class="error-card">Error fetching ${icao}: ${error.message}</div>`;
    } finally {
        button.disabled = false;
        button.textContent = 'Fetch';
    }
}

function getUTCtime() {
    const now = new Date();
    return `${String(now.getUTCHours()).padStart(2, '0')}:${String(now.getUTCMinutes()).padStart(2, '0')} UTC`;
}

async function fetchAndDisplayData() {
    const container = document.getElementById('airport-cards');
    container.innerHTML = '<div style="text-align: center; color: #5dade2; padding: 40px;">Loading data...</div>';

    const allAirports = [...mainAirports, ...secondaryAirports];
    const cards = [];

    for (const airport of allAirports) {
        const card = await fetchAirportData(airport);
        if (card) cards.push(card);
    }

    container.innerHTML = '';
    cards.forEach(card => container.appendChild(card));

    // Update timestamp
    document.getElementById('timestamp').textContent = `Last updated: ${getUTCtime()}`;
}

async function fetchAirportData(airportCode) {
    const url = `https://avwx.rest/api/metar/${airportCode}?token=vmtkb1D8Tuva2Jw2tXihWcKE3m2sfDJkySBZygVx82I`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Failed to fetch METAR for ${airportCode}`);

        const data = await response.json();
        const windDirectionTrue = parseInt(data.wind_direction?.value || 0, 10);
        const windSpeed = parseInt(data.wind_speed?.value || 0, 10);
        const gustSpeed = parseInt(data.wind_gust?.value || windSpeed, 10);

        const windDirectionMag = (windDirectionTrue + magneticVariation + 360) % 360;
        const effectiveWindSpeed = gustSpeed > windSpeed ? gustSpeed : windSpeed;

        // Calculate wind components for ALL runways
        const runwayData = [];
        let bestRunway = null;
        let bestHeadwind = -Infinity;
        let bestCrosswind = null;

        const airportRunways = runways[airportCode];
        
        if (!airportRunways || Object.keys(airportRunways).length === 0) {
            // No runway data available for this airport
            return createNoRunwayCard(airportCode, data, windDirectionMag, effectiveWindSpeed);
        }

        for (const [runway, heading] of Object.entries(airportRunways)) {
            const components = calculateWindComponents(windDirectionMag, effectiveWindSpeed, heading);
            runwayData.push({
                runway,
                heading,
                runwayNum: parseInt(runway),
                ...components
            });

            // Determine best runway
            if (components.headwind > bestHeadwind || 
                (components.headwind === bestHeadwind && Math.abs(components.crosswind) < Math.abs(bestCrosswind))) {
                bestHeadwind = components.headwind;
                bestCrosswind = components.crosswind;
                bestRunway = runway;
            }
        }

        // Sort runways by number and group reciprocals
        runwayData.sort((a, b) => a.runwayNum - b.runwayNum);
        
        // Group into reciprocal pairs
        const runwayPairs = [];
        const used = new Set();
        
        for (const rwy of runwayData) {
            if (used.has(rwy.runway)) continue;
            
            // Find reciprocal (runway number ± 18)
            const reciprocalNum = rwy.runwayNum <= 18 ? rwy.runwayNum + 18 : rwy.runwayNum - 18;
            const reciprocal = runwayData.find(r => r.runwayNum === reciprocalNum);
            
            if (reciprocal) {
                runwayPairs.push([rwy, reciprocal]);
                used.add(rwy.runway);
                used.add(reciprocal.runway);
            } else {
                runwayPairs.push([rwy]);
                used.add(rwy.runway);
            }
        }

        const metar = sanitizeMETAR(data.raw);
        const flightRules = data.flight_rules || "Unknown";
        const altimeter = data.altimeter?.repr || 'N/A';

        // Extract ceiling and visibility
        let ceiling = null;
        let visibility = null;

        // Get ceiling from clouds
        if (data.clouds && data.clouds.length > 0) {
            for (const cloud of data.clouds) {
                if (cloud.type === 'BKN' || cloud.type === 'OVC') {
                    ceiling = {
                        altitude: cloud.altitude,
                        type: cloud.type
                    };
                    break; // First BKN or OVC is the ceiling
                }
            }
        }

        // Get visibility (only show if IMC - less than 5SM)
        if (data.visibility && data.visibility.value) {
            const visValue = parseFloat(data.visibility.value);
            if (visValue < 5) {
                visibility = data.visibility.repr || `${visValue}SM`;
            }
        }

        return createAirportCard(airportCode, flightRules, windDirectionMag, effectiveWindSpeed, 
                                altimeter, metar, runwayPairs, bestRunway, ceiling, visibility);

    } catch (error) {
        console.error(`Error fetching data for ${airportCode}:`, error);
        return createErrorCard(airportCode, error.message);
    }
}

function calculateWindComponents(windDirection, windSpeed, runwayHeading) {
    const angle = ((windDirection - runwayHeading + 360) % 360) * (Math.PI / 180);
    const headwind = Math.round(windSpeed * Math.cos(angle));
    const crosswind = Math.round(windSpeed * Math.sin(angle));
    
    return {
        headwind,
        crosswind,
        crosswindAbs: Math.abs(crosswind)
    };
}

function createAirportCard(code, flightRules, windDir, windSpeed, altimeter, metar, runwayPairs, bestRunway, ceiling, visibility) {
    const card = document.createElement('div');
    card.className = 'airport-card';

    const flightRulesClass = flightRules.toLowerCase();

    // Build ceiling/visibility text inline
    let ceilingVisText = '';
    if (ceiling || visibility) {
        let infoItems = [];
        if (ceiling) {
            // Altitude from API is in hundreds of feet (METAR standard)
            // So ceiling.altitude < 10 means < 1000 feet (IMC)
            const isLowCeiling = ceiling.altitude < 10;
            const ceilingClass = isLowCeiling ? 'ceiling-vis-inline-warning' : 'ceiling-vis-inline';
            infoItems.push(`<span class="${ceilingClass}">CIG: ${ceiling.altitude} ${ceiling.type}</span>`);
        }
        if (visibility) {
            infoItems.push(`<span class="ceiling-vis-inline-warning">VIS: ${visibility}</span>`);
        }
        ceilingVisText = infoItems.join(' • ');
    }

    // Build runways HTML - each pair on one row
    const runwaysHTML = runwayPairs.map(pair => {
        return pair.map(rwy => {
            const isBest = rwy.runway === bestRunway;
            
            // Determine headwind/tailwind status
            let hwClass, hwArrow, hwValue;
            if (rwy.headwind >= 5) {
                hwClass = 'headwind';
                hwArrow = '↓';  // Headwind coming AT you
                hwValue = rwy.headwind;
            } else if (rwy.headwind >= 0) {
                hwClass = 'headwind';  // Changed from light-headwind to headwind (green)
                hwArrow = '↓';
                hwValue = rwy.headwind;
            } else if (rwy.headwind > -5) {
                hwClass = 'tailwind-mild';
                hwArrow = '↑';  // Tailwind pushing FROM BEHIND
                hwValue = Math.abs(rwy.headwind);
            } else {
                hwClass = 'tailwind-strong';
                hwArrow = '↑';
                hwValue = Math.abs(rwy.headwind);
            }

            // Determine crosswind status and direction
            let xwClass, xwArrow;
            if (rwy.crosswindAbs <= 12) {
                xwClass = 'crosswind-light';
            } else if (rwy.crosswindAbs <= 15) {
                xwClass = 'crosswind-moderate';
            } else {
                xwClass = 'crosswind-strong';
            }

            // Crosswind arrow shows FLOW of wind (vector direction)
            // Positive crosswind = wind from right, flowing left to right: →
            // Negative crosswind = wind from left, flowing right to left: ←
            xwArrow = rwy.crosswind > 0 ? '→' : '←';

            return `
                <div class="runway-item ${isBest ? 'best-choice' : ''}">
                    <div class="runway-number">${rwy.runway}</div>
                    <div class="wind-components">
                        <div class="wind-component ${hwClass}">
                            <span class="arrow">${hwArrow}</span>
                            <span>${hwValue}</span>
                        </div>
                        <div class="wind-component ${xwClass}">
                            <span class="arrow">${xwArrow}</span>
                            <span>${rwy.crosswindAbs}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }).join('');

    card.innerHTML = `
        <div class="airport-header">
            <div class="airport-code">${code}</div>
            <div class="flight-rules ${flightRulesClass}">${flightRules}</div>
        </div>
        
        <div class="wind-info">
            <div class="wind-direction">${windDir}°M/${windSpeed}</div>
            <div class="altimeter">${altimeter}</div>
            ${ceilingVisText}
        </div>

        <div class="runways-grid">
            ${runwaysHTML}
        </div>

        <div class="metar-section" onclick="this.classList.toggle('expanded')">
            <div class="metar-header">METAR <span class="metar-toggle">(click to show)</span></div>
            <div class="metar-text">${metar}</div>
        </div>
    `;

    return card;
}

function createErrorCard(airportCode, errorMessage) {
    const card = document.createElement('div');
    card.className = 'error-card';
    card.innerHTML = `
        <h3>${airportCode}</h3>
        <p>Error: ${errorMessage}</p>
    `;
    return card;
}

function createNoRunwayCard(airportCode, data, windDir, windSpeed) {
    const card = document.createElement('div');
    card.className = 'airport-card';
    
    const flightRules = data.flight_rules || "Unknown";
    const flightRulesClass = flightRules.toLowerCase();
    const altimeter = data.altimeter?.repr || 'N/A';
    const metar = sanitizeMETAR(data.raw);
    
    // Extract ceiling and visibility
    let ceiling = null;
    let visibility = null;
    
    if (data.clouds && data.clouds.length > 0) {
        for (const cloud of data.clouds) {
            if (cloud.type === 'BKN' || cloud.type === 'OVC') {
                ceiling = {
                    altitude: cloud.altitude,
                    type: cloud.type
                };
                break;
            }
        }
    }
    
    if (data.visibility && data.visibility.value) {
        const visValue = parseFloat(data.visibility.value);
        if (visValue < 5) {
            visibility = data.visibility.repr || `${visValue}SM`;
        }
    }
    
    // Build ceiling/visibility text
    let ceilingVisText = '';
    if (ceiling || visibility) {
        let infoItems = [];
        if (ceiling) {
            // Altitude from API is in hundreds of feet (METAR standard)
            // So ceiling.altitude < 10 means < 1000 feet (IMC)
            const isLowCeiling = ceiling.altitude < 10;
            const ceilingClass = isLowCeiling ? 'ceiling-vis-inline-warning' : 'ceiling-vis-inline';
            infoItems.push(`<span class="${ceilingClass}">CIG: ${ceiling.altitude} ${ceiling.type}</span>`);
        }
        if (visibility) {
            infoItems.push(`<span class="ceiling-vis-inline-warning">VIS: ${visibility}</span>`);
        }
        ceilingVisText = infoItems.join(' • ');
    }
    
    card.innerHTML = `
        <div class="airport-header">
            <div class="airport-code">${airportCode}</div>
            <div class="flight-rules ${flightRulesClass}">${flightRules}</div>
        </div>
        
        <div class="wind-info">
            <div class="wind-direction">${windDir}°M/${windSpeed}</div>
            <div class="altimeter">${altimeter}</div>
            ${ceilingVisText}
        </div>
        
        <div style="padding: 15px; text-align: center; color: #aaa; font-style: italic;">
            No runway data available for this airport
        </div>

        <div class="metar-section" onclick="this.classList.toggle('expanded')">
            <div class="metar-header">METAR <span class="metar-toggle">(click to show)</span></div>
            <div class="metar-text">${metar}</div>
        </div>
    `;
    
    return card;
}

function sanitizeMETAR(raw) {
    const altimeterPattern = /(A\d{4})/;
    const match = raw.match(altimeterPattern);
    return match ? raw.split(match[0])[0] + match[0] : raw;
}
