// METAR Runway Advisor — CZQM/CZQX FIR
// Card-based view with:
//  - MATS runway limits (TW ≤ 5kt, XW ≤ 25 dry / 15 wet)
//  - Wet detection from METAR wx_codes
//  - Preferred runway per airport
//  - CAT II / CAT IIIa approach awareness (low-ceiling fallback)
//  - Click runway to cycle role (off → ARR → DEP → A/D → off)
//  - Auto button: picks best config respecting all constraints

const mainAirports = ["CYHZ", "CYYT", "CYFC", "CYQM", "CYSJ", "CYQX", "CYZX", "CYYG", "CYYR"];
const secondaryAirports = ["CYQI", "CYAY", "CYDF", "CYJT", "LFVP"];
const magneticVariation = 18; // West variation for E Canada — add to true wind
const AVWX_TOKEN = 'vmtkb1D8Tuva2Jw2tXihWcKE3m2sfDJkySBZygVx82I';

const PRECIP_CODES = ['RA','SN','DZ','TS','SH','FZ','GR','GS','PL','IC','UP'];
const MAX_TAILWIND = 5;
const MAX_XW_DRY = 30;   // NAV CANADA MATS limit (updated from 25 to 30 per ATC MANOPS — matches atfm-tools v0.5.72+)
const MAX_XW_WET = 15;
const ROLE_CYCLE = ['off', 'A/D', 'A', 'D'];
// Single-runway A/D interleaved ops cap for ADR — per FAA FOA Ch.10 §7 /
// atfm-tools v0.6.20. One runway doing both arrivals AND departures can't
// deliver full declared dep rate alongside full arr rate; dep cap is
// ~12/hr (a ~2-min slot between interleaved arrivals).
const SINGLE_AD_DEP_CAP = 12;

// CAT thresholds (ceiling in hundreds of ft per METAR standard):
//  CAT I min  = 200 ft DH / 1800 RVR — ceiling ≥ 2 means CAT I suffices
//  CAT II min = 100 ft DH / 1200 RVR — ceiling < 2 needs CAT II
//  CAT III    = <100 ft DH           — ceiling < 1 needs CAT III
const CEIL_CAT_I  = 2;  // ceiling < 2 (200 ft) forces CAT II+
const CEIL_CAT_II = 1;  // ceiling < 1 (100 ft) forces CAT III

// ===================================================================
// CONFIGS — runway configurations per airport, mirrors atfm-tools
// runway-configs.json structure. Each airport has:
//   preferred: default runway for calm winds
//   configs:   list of operational configs (single-runway or LAHSO)
// Rates are physics-derived per docs/RATES-VALIDATION.md §0 methodology:
//   single interleaved   = balanced AAR = ADR, total 36–44/hr
//   LAHSO (arr+crossing) = 26A / 22D (primary arr released from dep
//                          demand, dep strip mostly independent modulo
//                          intersection dependency)
// Wake mix assumption: all CZQM/CZQX airports are medium-dominant
// (no haircut), except CYYT at ~10% Heavy → ~6% haircut applied.
// CYHZ values mirror atfm-tools data/runway-configs.json to keep the
// two projects in lockstep.
// ===================================================================
const CONFIGS = {
    CYHZ: {
        // CYHZ operational notes (mirrors atfm-tools v0.5.76+):
        //   14 has ILS — preferred arrival in IMC (CAT I). 05/23 are
        //   longer and preferred for heavy departures. Dependent-dep
        //   configs (14 arr + 05 dep, 14 arr + 23 dep, 32 arr + 05 dep)
        //   give the tower a heavy-dep release option while keeping ILS
        //   arrivals on 14.
        preferred: "23",
        configs: [
            { name: "23", label: "23 Single", mode: "single",
              runways: { "23": "A/D" }, arr: 22, dep: 22 },
            { name: "05", label: "05 Single", mode: "single",
              runways: { "05": "A/D" }, arr: 22, dep: 22 },
            { name: "14", label: "14 Single (ILS)", mode: "single", ils: true,
              runways: { "14": "A/D" }, arr: 18, dep: 18 },
            { name: "14-05dep", label: "14 Arr (ILS) / 05 Dep", mode: "dependent",
              ils: true, runways: { "14": "A", "05": "D" }, arr: 22, dep: 22 },
            { name: "14-23dep", label: "14 Arr (ILS) / 23 Dep", mode: "dependent",
              ils: true, runways: { "14": "A", "23": "D" }, arr: 22, dep: 22 },
            { name: "32", label: "32 Single", mode: "single",
              runways: { "32": "A/D" }, arr: 18, dep: 18 },
            { name: "32-05dep", label: "32 Arr / 05 Dep", mode: "dependent",
              runways: { "32": "A", "05": "D" }, arr: 22, dep: 22 },
            { name: "05-LAHSO-14", label: "05 Arr / 14 Dep (LAHSO)",
              mode: "lahso", requires: { dry: true, vmc: true },
              runways: { "05": "A", "14": "D" }, arr: 26, dep: 22 },
            { name: "05-LAHSO-32", label: "05 Arr / 32 Dep (LAHSO)",
              mode: "lahso", requires: { dry: true, vmc: true },
              runways: { "05": "A", "32": "D" }, arr: 26, dep: 22 }
        ]
    },
    CYYT: {
        // 10% Heavy mix → ~6% haircut from ceiling values
        preferred: null,
        configs: [
            { name: "10", label: "10 Single", mode: "single",
              runways: { "10": "A/D" }, arr: 21, dep: 21 },
            { name: "28", label: "28 Single", mode: "single",
              runways: { "28": "A/D" }, arr: 21, dep: 21 },
            { name: "16", label: "16 Single", mode: "single",
              runways: { "16": "A/D" }, arr: 19, dep: 19 },
            { name: "34", label: "34 Single", mode: "single",
              runways: { "34": "A/D" }, arr: 19, dep: 19 }
        ]
    },
    CYFC: {
        preferred: null,
        configs: [
            { name: "09", label: "09 Single", mode: "single",
              runways: { "09": "A/D" }, arr: 20, dep: 20 },
            { name: "27", label: "27 Single", mode: "single",
              runways: { "27": "A/D" }, arr: 20, dep: 20 },
            { name: "15", label: "15 Single", mode: "single",
              runways: { "15": "A/D" }, arr: 18, dep: 18 },
            { name: "33", label: "33 Single", mode: "single",
              runways: { "33": "A/D" }, arr: 18, dep: 18 }
        ]
    },
    CYQM: {
        preferred: null,
        configs: [
            { name: "06", label: "06 Single", mode: "single",
              runways: { "06": "A/D" }, arr: 20, dep: 20 },
            { name: "24", label: "24 Single", mode: "single",
              runways: { "24": "A/D" }, arr: 20, dep: 20 },
            { name: "11", label: "11 Single", mode: "single",
              runways: { "11": "A/D" }, arr: 18, dep: 18 },
            { name: "29", label: "29 Single", mode: "single",
              runways: { "29": "A/D" }, arr: 18, dep: 18 },
            // LAHSO: 24 arr holds short of 11/29 intersection,
            // 11 or 29 dep runs independently per wind
            { name: "24-LAHSO-11", label: "24 Arr / 11 Dep (LAHSO HS 11/29)",
              mode: "lahso", requires: { dry: true, vmc: true },
              runways: { "24": "A", "11": "D" }, arr: 26, dep: 22 },
            { name: "24-LAHSO-29", label: "24 Arr / 29 Dep (LAHSO HS 11/29)",
              mode: "lahso", requires: { dry: true, vmc: true },
              runways: { "24": "A", "29": "D" }, arr: 26, dep: 22 }
        ]
    },
    CYSJ: {
        preferred: null,
        configs: [
            { name: "05", label: "05 Single", mode: "single",
              runways: { "05": "A/D" }, arr: 20, dep: 20 },
            { name: "23", label: "23 Single", mode: "single",
              runways: { "23": "A/D" }, arr: 20, dep: 20 },
            { name: "14", label: "14 Single", mode: "single",
              runways: { "14": "A/D" }, arr: 18, dep: 18 },
            { name: "32", label: "32 Single", mode: "single",
              runways: { "32": "A/D" }, arr: 18, dep: 18 }
        ]
    },
    CYZX: {
        preferred: null,
        configs: [
            { name: "08", label: "08 Single", mode: "single",
              runways: { "08": "A/D" }, arr: 18, dep: 18 },
            { name: "26", label: "26 Single", mode: "single",
              runways: { "26": "A/D" }, arr: 18, dep: 18 },
            { name: "12", label: "12 Single", mode: "single",
              runways: { "12": "A/D" }, arr: 18, dep: 18 },
            { name: "30", label: "30 Single", mode: "single",
              runways: { "30": "A/D" }, arr: 18, dep: 18 }
        ]
    },
    CYYG: {
        preferred: null,
        configs: [
            { name: "03", label: "03 Single", mode: "single",
              runways: { "03": "A/D" }, arr: 18, dep: 18 },
            { name: "21", label: "21 Single", mode: "single",
              runways: { "21": "A/D" }, arr: 18, dep: 18 },
            { name: "10", label: "10 Single", mode: "single",
              runways: { "10": "A/D" }, arr: 18, dep: 18 },
            { name: "28", label: "28 Single", mode: "single",
              runways: { "28": "A/D" }, arr: 18, dep: 18 }
        ]
    },
    CYQX: {
        // Gander — 03/21 is the long transatlantic strip (10,500 ft)
        preferred: null,
        configs: [
            { name: "03", label: "03 Single", mode: "single",
              runways: { "03": "A/D" }, arr: 22, dep: 22 },
            { name: "21", label: "21 Single", mode: "single",
              runways: { "21": "A/D" }, arr: 22, dep: 22 },
            { name: "13", label: "13 Single", mode: "single",
              runways: { "13": "A/D" }, arr: 20, dep: 20 },
            { name: "31", label: "31 Single", mode: "single",
              runways: { "31": "A/D" }, arr: 20, dep: 20 }
        ]
    },
    CYYR: {
        // Goose Bay — 08/26 is the long USAF strip (~11,000 ft)
        preferred: null,
        configs: [
            { name: "08", label: "08 Single", mode: "single",
              runways: { "08": "A/D" }, arr: 22, dep: 22 },
            { name: "26", label: "26 Single", mode: "single",
              runways: { "26": "A/D" }, arr: 22, dep: 22 },
            { name: "15", label: "15 Single", mode: "single",
              runways: { "15": "A/D" }, arr: 20, dep: 20 },
            { name: "33", label: "33 Single", mode: "single",
              runways: { "33": "A/D" }, arr: 20, dep: 20 }
        ]
    },
    // Secondary airports — single-runway or 4-runway small fields
    CYQI: {
        preferred: null,
        configs: [
            { name: "06", label: "06 Single", mode: "single", runways: { "06": "A/D" }, arr: 18, dep: 18 },
            { name: "24", label: "24 Single", mode: "single", runways: { "24": "A/D" }, arr: 18, dep: 18 },
            { name: "15", label: "15 Single", mode: "single", runways: { "15": "A/D" }, arr: 18, dep: 18 },
            { name: "33", label: "33 Single", mode: "single", runways: { "33": "A/D" }, arr: 18, dep: 18 }
        ]
    },
    CYAY: { preferred: null, configs: [
        { name: "10", label: "10 Single", mode: "single", runways: { "10": "A/D" }, arr: 18, dep: 18 },
        { name: "28", label: "28 Single", mode: "single", runways: { "28": "A/D" }, arr: 18, dep: 18 }
    ]},
    CYDF: { preferred: null, configs: [
        { name: "07", label: "07 Single", mode: "single", runways: { "07": "A/D" }, arr: 18, dep: 18 },
        { name: "25", label: "25 Single", mode: "single", runways: { "25": "A/D" }, arr: 18, dep: 18 }
    ]},
    CYJT: { preferred: null, configs: [
        { name: "09", label: "09 Single", mode: "single", runways: { "09": "A/D" }, arr: 18, dep: 18 },
        { name: "27", label: "27 Single", mode: "single", runways: { "27": "A/D" }, arr: 18, dep: 18 }
    ]},
    LFVP: { preferred: null, configs: [
        { name: "08", label: "08 Single", mode: "single", runways: { "08": "A/D" }, arr: 18, dep: 18 },
        { name: "26", label: "26 Single", mode: "single", runways: { "26": "A/D" }, arr: 18, dep: 18 }
    ]}
};

// Runway metadata per airport (heading + approach CAT only).
//   hdg: magnetic heading
//   cat: highest approach cat (1 | 2 | 3) — default 1
// Airport-level:
//   preferred: (also in CONFIGS for autoPropose)
const runways = {
    CYHZ: {
        preferred: "23",
        // LAHSO directional: only 05 can land-and-hold-short (of 14 or 32).
        // The reverse is not operationally possible — intersection geometry
        // doesn't give 14/32 arrivals enough rollout before crossing 05.
        lahso: { "05": ["14", "32"] },
        rwys: {
            "05": { hdg: 53,  cat: 1 },
            "23": { hdg: 233, cat: 2 },   // CAT II on 23 (low-ceiling fallback)
            "14": { hdg: 143, cat: 1 },
            "32": { hdg: 323, cat: 1 }
        }
    },
    CYYT: {
        preferred: null,
        rwys: {
            "10": { hdg: 103, cat: 3 },   // CAT II/IIIA on 10
            "28": { hdg: 283, cat: 3 },   // CAT II/IIIA on 28
            "16": { hdg: 156, cat: 1 },
            "34": { hdg: 336, cat: 1 }
        }
    },
    CYFC: {
        preferred: null,
        rwys: {
            "09": { hdg: 87,  cat: 1 },
            "15": { hdg: 148, cat: 1 },
            "27": { hdg: 268, cat: 1 },
            "33": { hdg: 328, cat: 1 }
        }
    },
    CYQM: {
        preferred: null,
        // LAHSO directional: only 24 can hold short (of 11 or 29).
        lahso: { "24": ["11", "29"] },
        rwys: {
            "06": { hdg: 61,  cat: 1 },
            "29": { hdg: 286, cat: 1 },
            "11": { hdg: 106, cat: 1 },
            "24": { hdg: 241, cat: 1 }
        }
    },
    CYSJ: {
        preferred: null,
        rwys: {
            "23": { hdg: 229, cat: 1 },
            "05": { hdg: 49,  cat: 1 },
            "14": { hdg: 138, cat: 1 },
            "32": { hdg: 319, cat: 1 }
        }
    },
    CYZX: {
        preferred: null,
        rwys: {
            "08": { hdg: 80,  cat: 1 },
            "12": { hdg: 122, cat: 1 },
            "26": { hdg: 261, cat: 1 },
            "30": { hdg: 303, cat: 1 }
        }
    },
    CYYG: {
        preferred: null,
        rwys: {
            "03": { hdg: 27,  cat: 1 },
            "21": { hdg: 207, cat: 1 },
            "10": { hdg: 97,  cat: 1 },
            "28": { hdg: 277, cat: 1 }
        }
    },
    CYQX: {
        preferred: null,
        rwys: {
            "21": { hdg: 210, cat: 1 },
            "03": { hdg: 30,  cat: 1 },
            "13": { hdg: 128, cat: 1 },
            "31": { hdg: 308, cat: 1 }
        }
    },
    CYYR: {
        preferred: null,
        rwys: {
            "15": { hdg: 153, cat: 1 },
            "33": { hdg: 333, cat: 1 },
            "08": { hdg: 75,  cat: 1 },
            "26": { hdg: 255, cat: 1 }
        }
    },
    LFVP: { preferred: null, rwys: {
        "08": { hdg: 76, cat: 1 }, "26": { hdg: 256, cat: 1 }
    }},
    CYQI: { preferred: null, rwys: {
        "06": { hdg: 59, cat: 1 }, "15": { hdg: 150, cat: 1 },
        "24": { hdg: 239, cat: 1 }, "33": { hdg: 330, cat: 1 }
    }},
    CYAY: { preferred: null, rwys: {
        "10": { hdg: 99, cat: 1 }, "28": { hdg: 279, cat: 1 }
    }},
    CYDF: { preferred: null, rwys: {
        "25": { hdg: 244, cat: 1 }, "07": { hdg: 64, cat: 1 }
    }},
    CYJT: { preferred: null, rwys: {
        "27": { hdg: 270, cat: 1 }, "09": { hdg: 90, cat: 1 }
    }}
};

// Live per-airport state built on each fetch
const aptState = {};

// =========== Init ===========

document.addEventListener('DOMContentLoaded', () => {
    fetchAndDisplayData();
    setInterval(fetchAndDisplayData, 15 * 60 * 1000);
    setupAdhocMetar();
    setupHelpModal();
});

document.getElementById('refresh-btn').addEventListener('click', () => {
    const btn = document.getElementById('refresh-btn');
    btn.classList.add('loading');
    fetchAndDisplayData().finally(() => btn.classList.remove('loading'));
});

function setupHelpModal() {
    const modal = document.getElementById('help-modal');
    const helpBtn = document.getElementById('help-btn');
    const closeBtn = document.querySelector('.modal-close');
    helpBtn.addEventListener('click', () => modal.classList.add('show'));
    closeBtn.addEventListener('click', () => modal.classList.remove('show'));
    modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('show'); });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && modal.classList.contains('show')) modal.classList.remove('show');
    });
}

function setupAdhocMetar() {
    const input = document.getElementById('adhoc-icao');
    const button = document.getElementById('adhoc-fetch');
    button.addEventListener('click', () => fetchAdhocMetar());
    input.addEventListener('keypress', e => { if (e.key === 'Enter') fetchAdhocMetar(); });
    input.addEventListener('input', e => { e.target.value = e.target.value.toUpperCase(); });
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
    resultDiv.innerHTML = '<div style="color: var(--accent); padding: 20px; text-align: center;">Fetching data...</div>';
    try {
        const response = await fetch(`https://avwx.rest/api/metar/${icao}?token=${AVWX_TOKEN}`);
        if (!response.ok) throw new Error(`Failed to fetch METAR for ${icao}`);
        const data = await response.json();
        const metar = data.raw || 'No METAR available';
        resultDiv.innerHTML = `
            <div class="adhoc-metar-display">
                <div class="adhoc-metar-header">${icao} METAR</div>
                <div class="adhoc-metar-text">${metar}</div>
            </div>`;
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

// =========== Physics ===========

function calculateWindComponents(windDir, windSpeed, rwyHdg) {
    const angle = ((windDir - rwyHdg + 360) % 360) * (Math.PI / 180);
    const headwind = Math.round(windSpeed * Math.cos(angle));
    const crosswind = Math.round(windSpeed * Math.sin(angle));
    return { headwind, crosswind, crosswindAbs: Math.abs(crosswind) };
}

function isWet(data) {
    if (!data || !data.wx_codes) return false;
    return data.wx_codes.some(wx => {
        const s = (wx.repr || wx.value || '').toUpperCase();
        return PRECIP_CODES.some(p => s.includes(p));
    });
}

function rwyAvailable(hw, xwAbs, wet) {
    if (hw < -MAX_TAILWIND) return { avail: false, reason: `TW ${Math.abs(hw)} > ${MAX_TAILWIND}kt` };
    const xwLimit = wet ? MAX_XW_WET : MAX_XW_DRY;
    if (xwAbs > xwLimit) return { avail: false, reason: `XW ${xwAbs} > ${xwLimit}kt${wet ? ' wet' : ''}` };
    return { avail: true, reason: '' };
}

// Reciprocal: 08 ↔ 26, 05 ↔ 23 — add/subtract 18, flip L/R suffix
function reciprocalIdent(id) {
    const m = id.match(/^(\d+)(L|R|C)?$/);
    if (!m) return null;
    const num = parseInt(m[1]);
    const sfx = m[2] || '';
    const rNum = num <= 18 ? num + 18 : num - 18;
    const rSfx = sfx === 'L' ? 'R' : sfx === 'R' ? 'L' : sfx;
    return String(rNum).padStart(2, '0') + rSfx;
}

// =========== Auto-propose ===========

function requiredCat(ceilingHundreds) {
    if (ceilingHundreds === null) return 1;
    // At the category minima (200 ft / 100 ft) you're already committed
    // to that category — an approach to CAT I minima of 200 ft IS a
    // CAT I approach, so ceiling ≤ 200 forces CAT II, ceiling ≤ 100
    // forces CAT III.
    if (ceilingHundreds <= CEIL_CAT_II) return 3;
    if (ceilingHundreds <= CEIL_CAT_I)  return 2;
    return 1;
}

function autoPropose(icao) {
    const st = aptState[icao];
    if (!st) return;

    // Clear all roles and reset rates
    for (const r of Object.values(st.runways)) { r.role = 'off'; r.lahso = false; }
    st.arrRate = null;
    st.depRate = null;
    st.selectedConfig = null;

    const reqCat = requiredCat(st.ceilingHundreds);
    const aptCfg = CONFIGS[icao];
    const preferred = aptCfg?.preferred || null;
    const vmc = (st.rules === 'VFR' || st.rules === 'MVFR');

    // CONFIGS-based selection: walk the configs list, filter by weather
    // (LAHSO needs dry + VMC) and runway availability, score by headwind
    // on primary arr runway with preferred-runway bonus. CAT fallback
    // applies: if ceiling requires CAT II+, the primary_arr runway must
    // be CAT-capable at that level.
    if (aptCfg && aptCfg.configs) {
        let best = null, bestScore = -Infinity;
        for (const cfg of aptCfg.configs) {
            // Weather gating
            if (cfg.requires) {
                if (cfg.requires.dry && st.wet) continue;
                if (cfg.requires.vmc && !vmc) continue;
            }
            // All runways in the config must be available; any runway
            // carrying an arrival role must also be CAT-capable (not noArr).
            let ok = true, primaryArrId = null;
            for (const [id, role] of Object.entries(cfg.runways)) {
                const r = st.runways[id];
                if (!r || !r.avail) { ok = false; break; }
                if (role === 'A' || role === 'A/D') {
                    if (r.noArr) { ok = false; break; }
                    primaryArrId = primaryArrId || id;
                }
            }
            if (!ok) continue;
            const primaryArr = st.runways[primaryArrId];
            if (!primaryArr) continue;

            // Composite score (mirrors atfm-tools v0.5.74-v0.5.76):
            //   score = declared_rate + max(0,hw) × 0.5 + ILS bonus(+3
            //           in IFR/LIFR) + preferred bonus (+10, VMC only)
            // Rate weight keeps higher-capacity configs ahead.
            // Headwind bonus lets a well-aligned lower-rate config
            // beat a poorly-aligned higher-rate one. ILS bonus in
            // IFR ensures CAT-capable runway (e.g. CYHZ 14) wins
            // when the ceiling is low. Preferred-runway bonus only
            // applies in VMC — in IFR/LIFR we want the ILS runway to
            // win even if it's not the calm-wind preferred choice
            // (aligns with atfm-tools, which has no preferred concept
            //  and picks ILS in IMC by design).
            const hwBonus = Math.max(0, primaryArr.hw) * 0.5;
            const ifr = (st.rules === 'IFR' || st.rules === 'LIFR');
            const vmc = !ifr;
            const ilsBonus = (ifr && cfg.ils) ? 3 : 0;
            const prefBonus = (vmc && primaryArrId === preferred) ? 10 : 0;
            let score = (cfg.arr || 0) + hwBonus + ilsBonus + prefBonus;
            if (score > bestScore) { bestScore = score; best = cfg; }
        }

        if (best) {
            for (const [id, role] of Object.entries(best.runways)) {
                if (st.runways[id]) st.runways[id].role = role;
            }
            st.selectedConfig = best;
            // Single-runway A/D interleave cap — a single runway can't
            // deliver both declared arr AND declared dep rates; cap
            // ADR at SINGLE_AD_DEP_CAP (per atfm-tools v0.6.20).
            const rwyIds = Object.keys(best.runways);
            const isSingleAD = rwyIds.length === 1 && best.runways[rwyIds[0]] === 'A/D';
            st.arrRate = best.arr;
            st.depRate = isSingleAD ? Math.min(best.dep, SINGLE_AD_DEP_CAP) : best.dep;
            st.configName = best.label;
            flagLahsoFromTopology(icao);
            return;
        }
    }

    // Fallback 1: no config matched but at least one runway is available
    // and arr-capable. Pick best by headwind.
    const candidates = Object.entries(st.runways)
        .filter(([, r]) => r.avail && !r.noArr);
    if (candidates.length) {
        let bestId = null, bestHw = -999, bestXw = 999;
        for (const [id, r] of candidates) {
            if (r.hw > bestHw || (r.hw === bestHw && r.crosswindAbs < bestXw)) {
                bestHw = r.hw; bestXw = r.crosswindAbs; bestId = id;
            }
        }
        if (bestId) {
            st.runways[bestId].role = 'A/D';
            st.configName = `${bestId} (fallback)`;
            return;
        }
    }

    // Fallback 2 (least-worst, per atfm-tools v0.5.78): all runways
    // exceed hard MATS limits. An airport can't close over a few kts
    // of extra crosswind — pick the runway with smallest combined
    // excess (tailwind excess weighted 2× since it's worse for
    // stopping). Flagged as "over limits" so controller sees the
    // compromise explicitly.
    const xwLimit = st.wet ? MAX_XW_WET : MAX_XW_DRY;
    const scoreRwy = r => {
        const tailExcess = Math.max(0, -r.hw - MAX_TAILWIND);
        const xwExcess = Math.max(0, r.crosswindAbs - xwLimit);
        return tailExcess * 2 + xwExcess;
    };
    let leastWorst = null, leastScore = 999;
    for (const [id, r] of Object.entries(st.runways)) {
        if (r.noArr) continue; // arr-capable first pass
        const s = scoreRwy(r);
        if (s < leastScore) { leastScore = s; leastWorst = id; }
    }
    // If no arr-capable runway, try any
    if (!leastWorst) {
        for (const [id, r] of Object.entries(st.runways)) {
            const s = scoreRwy(r);
            if (s < leastScore) { leastScore = s; leastWorst = id; }
        }
    }
    if (leastWorst) {
        st.runways[leastWorst].role = 'A/D';
        st.configName = `${leastWorst} (over limits)`;
    } else {
        st.configName = reqCat > 1 ? `No CAT ${reqCat} available` : 'No runway available';
    }
}

// LAHSO is directional and airport-specific (published per-runway in CFS
// / unit SOP). A runway is flagged LAHSO only when:
//   1. Its role is A or A/D (it's taking arrivals)
//   2. The airport's lahso spec declares it capable of holding short
//   3. At least one of its hold-short target runways is currently active
// The target runway itself is NOT flagged — only the runway doing the
// hold-short performs the LAHSO action. E.g. CYHZ 05 can LAHSO of 14,
// but 14 cannot LAHSO of 05 (intersection geometry).
function flagLahsoFromTopology(icao) {
    const st = aptState[icao];
    if (!st || !st.runways) return;
    // Clear all flags first
    for (const r of Object.values(st.runways)) r.lahso = false;

    const spec = runways[icao]?.lahso;
    if (!spec) return;

    for (const [holdShortId, targets] of Object.entries(spec)) {
        const hsRwy = st.runways[holdShortId];
        if (!hsRwy) continue;
        if (hsRwy.role !== 'A' && hsRwy.role !== 'A/D') continue;
        // At least one target must be active for LAHSO to be in effect
        for (const tgt of targets) {
            const tgtRwy = st.runways[tgt];
            if (tgtRwy && tgtRwy.role && tgtRwy.role !== 'off') {
                hsRwy.lahso = true;
                break;
            }
        }
    }
}

function recomputeRates(icao) {
    const st = aptState[icao];
    if (!st || !st.runways) return;

    // Build active runway map {id: role} and clear any stale LAHSO flags
    const active = {};
    for (const [id, r] of Object.entries(st.runways)) {
        r.lahso = false;
        if (r.role && r.role !== 'off') active[id] = r.role;
    }
    const activeIds = Object.keys(active).sort();
    if (!activeIds.length) {
        st.arrRate = null;
        st.depRate = null;
        st.configName = 'No runway selected';
        return;
    }

    // Try to find an exact config match (same runway set + same roles)
    const aptCfg = CONFIGS[icao];
    if (aptCfg && aptCfg.configs) {
        for (const cfg of aptCfg.configs) {
            const cfgIds = Object.keys(cfg.runways).sort();
            if (cfgIds.length !== activeIds.length) continue;
            let match = true;
            for (const id of cfgIds) {
                if (active[id] !== cfg.runways[id]) { match = false; break; }
            }
            if (match) {
                st.arrRate = cfg.arr;
                // Single-runway A/D cap — see autoPropose comment
                const rwyIds = Object.keys(cfg.runways);
                const isSingleAD = rwyIds.length === 1 && cfg.runways[rwyIds[0]] === 'A/D';
                st.depRate = isSingleAD ? Math.min(cfg.dep, SINGLE_AD_DEP_CAP) : cfg.dep;
                st.configName = cfg.label;
                flagLahsoFromTopology(icao);
                return;
            }
        }
    }

    // No matching published config — derive from physics with dependency
    // modeling. Each active strip contributes an isolated ceiling based on
    // its role. Strips are grouped into heading families (mod 180, within
    // 15°): parallels are independent and their rates sum; crossing
    // families share the intersection window and the secondary family
    // contributes at a 20% discount (each crossing op blocks the primary
    // for ~1 slot, so the net uplift is small).
    const is25NM = (icao === 'CYVR' || icao === 'CYYZ');
    function stripRates(role) {
        // Single A/D dep is capped at SINGLE_AD_DEP_CAP (12) per FAA
        // interleave; the 22-dep value would only be deliverable on a
        // dedicated-dep runway (role = D).
        if (role === 'A/D') return { arr: 22, dep: SINGLE_AD_DEP_CAP };
        if (role === 'A')   return { arr: is25NM ? 46 : 42, dep: 0 };
        if (role === 'D')   return { arr: 0, dep: 30 };
        return { arr: 0, dep: 0 };
    }

    // Group by heading family
    const families = []; // {hdg, arr, dep}
    for (const [id, role] of Object.entries(active)) {
        const rwy = st.runways[id];
        if (!rwy) continue;
        const fam = ((rwy.hdg % 180) + 180) % 180;
        let m = null;
        for (const f of families) {
            const raw = Math.abs(f.hdg - fam);
            const diff = Math.min(raw, 180 - raw);
            if (diff < 15) { m = f; break; }
        }
        if (!m) { m = { hdg: fam, arr: 0, dep: 0 }; families.push(m); }
        const sr = stripRates(role);
        m.arr += sr.arr;
        m.dep += sr.dep;
    }

    if (!families.length) {
        st.arrRate = null;
        st.depRate = null;
        st.configName = 'No runway selected';
        return;
    }

    // Pick the family with the highest total mvts as primary
    let primary = families[0];
    for (const f of families) {
        if ((f.arr + f.dep) > (primary.arr + primary.dep)) primary = f;
    }

    // Combine: primary in full + 0.2 × each secondary family
    let arr = primary.arr, dep = primary.dep;
    for (const f of families) {
        if (f === primary) continue;
        arr += f.arr * 0.2;
        dep += f.dep * 0.2;
    }

    st.arrRate = Math.round(arr);
    st.depRate = Math.round(dep);
    st.configName = families.length > 1
        ? 'Manual — dependent crossing ops'
        : 'Manual';
    flagLahsoFromTopology(icao);
}

function toggleRwy(icao, ident) {
    const st = aptState[icao];
    if (!st || !st.runways[ident] || !st.runways[ident].avail) return;
    const r = st.runways[ident];
    let next = ROLE_CYCLE[(ROLE_CYCLE.indexOf(r.role) + 1) % ROLE_CYCLE.length];
    // Skip arrival roles on runways that can't accept arrivals (CAT shortfall)
    let guard = 0;
    while (r.noArr && (next === 'A' || next === 'A/D') && guard++ < ROLE_CYCLE.length) {
        next = ROLE_CYCLE[(ROLE_CYCLE.indexOf(next) + 1) % ROLE_CYCLE.length];
    }
    r.role = next;
    // Activating one end turns off the opposite end (same strip)
    if (r.role !== 'off') {
        const rid = reciprocalIdent(ident);
        if (rid && st.runways[rid] && st.runways[rid].role !== 'off') {
            st.runways[rid].role = 'off';
        }
    }
    recomputeRates(icao);
    refreshCard(icao);
}

function proposeAuto(icao) {
    autoPropose(icao);
    refreshCard(icao);
}

function refreshCard(icao) {
    const card = document.querySelector(`[data-card="${icao}"]`);
    if (card) card.innerHTML = renderCardInner(icao);
}

// Expose handlers to inline onclick
window.toggleRwy = toggleRwy;
window.proposeAuto = proposeAuto;

// =========== Fetch ===========

async function fetchAndDisplayData() {
    const container = document.getElementById('airport-cards');
    container.innerHTML = '<div style="text-align: center; color: var(--accent); padding: 40px;">Loading data...</div>';

    const allAirports = [...mainAirports, ...secondaryAirports];
    const results = await Promise.all(allAirports.map(icao => fetchAirportData(icao)));

    container.innerHTML = '';
    for (let i = 0; i < allAirports.length; i++) {
        const icao = allAirports[i];
        if (results[i] === 'error') {
            container.appendChild(createErrorCard(icao, 'Failed to fetch METAR'));
            continue;
        }
        const card = document.createElement('div');
        card.className = 'airport-card';
        card.setAttribute('data-card', icao);
        card.innerHTML = renderCardInner(icao);
        container.appendChild(card);
    }
    document.getElementById('timestamp').textContent = `Last updated: ${getUTCtime()}`;
}

async function fetchAirportData(airportCode) {
    try {
        const response = await fetch(`https://avwx.rest/api/metar/${airportCode}?token=${AVWX_TOKEN}`);
        if (!response.ok) throw new Error(`Failed to fetch METAR for ${airportCode}`);
        const data = await response.json();

        const windDirectionTrue = parseInt(data.wind_direction?.value || 0, 10);
        const windSpeed = parseInt(data.wind_speed?.value || 0, 10);
        const gustSpeed = parseInt(data.wind_gust?.value || windSpeed, 10);
        const windDirectionMag = (windDirectionTrue + magneticVariation + 360) % 360;
        const effectiveWindSpeed = gustSpeed > windSpeed ? gustSpeed : windSpeed;

        const wet = isWet(data);

        // Ceiling: VV (indefinite / obscured sky) trumps BKN/OVC — if the
        // sky is obscured, VV is the definitive ceiling. Fall back to the
        // first BKN/OVC layer. Also parse VV from raw METAR as a safety
        // net in case AVWX puts it in an unexpected field.
        let ceilingHundreds = null;
        let ceilingType = null;
        if (data.clouds && data.clouds.length) {
            // Pass 1 — look for VV (indefinite ceiling)
            for (const c of data.clouds) {
                if (c.type === 'VV') {
                    ceilingHundreds = c.altitude;
                    ceilingType = 'VV';
                    break;
                }
            }
            // Pass 2 — first BKN/OVC if no VV
            if (ceilingHundreds === null) {
                for (const c of data.clouds) {
                    if (c.type === 'BKN' || c.type === 'OVC') {
                        ceilingHundreds = c.altitude;
                        ceilingType = c.type;
                        break;
                    }
                }
            }
        }
        // Raw-METAR fallback for VVnnn (e.g. VV002 = 200 ft indefinite).
        // Catches cases where AVWX didn't surface the VV layer in clouds[].
        if (ceilingHundreds === null && data.raw) {
            const vvMatch = data.raw.match(/\bVV(\d{3})\b/);
            if (vvMatch) {
                ceilingHundreds = parseInt(vvMatch[1], 10);
                ceilingType = 'VV';
            }
        }

        // Visibility — only surface if IMC (< 5SM)
        let visibility = null;
        if (data.visibility && data.visibility.value) {
            const v = parseFloat(data.visibility.value);
            if (v < 5) visibility = data.visibility.repr || `${v}SM`;
        }

        const meta = runways[airportCode];
        if (!meta || !Object.keys(meta.rwys).length) {
            aptState[airportCode] = {
                noRunway: true,
                rules: data.flight_rules || 'Unknown',
                altimeter: data.altimeter?.repr || 'N/A',
                windDir: windDirectionMag, windSpd: effectiveWindSpeed,
                wet, ceilingHundreds, ceilingType, visibility,
                metar: sanitizeMETAR(data.raw)
            };
            return 'ok';
        }

        const reqCat = requiredCat(ceilingHundreds);
        const rwys = {};
        for (const [ident, info] of Object.entries(meta.rwys)) {
            const wc = calculateWindComponents(windDirectionMag, effectiveWindSpeed, info.hdg);
            const availCheck = rwyAvailable(wc.headwind, wc.crosswindAbs, wet);
            const cat = info.cat || 1;
            // CAT shortfall: runway can't accept arrivals if its cat < reqCat,
            // but departures still allowed (takeoff minima are much lower
            // than landing minima). noArr = true prevents role cycle from
            // landing on A or A/D.
            const noArr = cat < reqCat;
            const noArrReason = noArr ? `CAT ${reqCat} required — arrivals not permitted` : null;
            rwys[ident] = {
                hdg: info.hdg,
                cat,
                hw: wc.headwind,
                xw: wc.crosswind,
                crosswindAbs: wc.crosswindAbs,
                avail: availCheck.avail,
                unavailReason: availCheck.reason,
                noArr,
                noArrReason,
                role: 'off'
            };
        }

        aptState[airportCode] = {
            rules: data.flight_rules || 'Unknown',
            altimeter: data.altimeter?.repr || 'N/A',
            windDir: windDirectionMag,
            windSpd: effectiveWindSpeed,
            wet,
            ceilingHundreds, ceilingType, visibility,
            runways: rwys,
            metar: sanitizeMETAR(data.raw),
            configName: ''
        };
        autoPropose(airportCode);
        return 'ok';
    } catch (error) {
        console.error(`Error fetching ${airportCode}:`, error);
        return 'error';
    }
}

// =========== Render ===========

function roleBadge(role) {
    if (role === 'A')   return '<span class="rwy-role-badge role-badge-A">ARR</span>';
    if (role === 'D')   return '<span class="rwy-role-badge role-badge-D">DEP</span>';
    if (role === 'A/D') return '<span class="rwy-role-badge role-badge-AD">A/D</span>';
    return '<span class="rwy-role-badge role-badge-off">OFF</span>';
}

// CAT badges: always show each capability the runway has (II if cat>=2,
// III if cat>=3). A badge lights when that category is actually the
// minimum required for the current ceiling — otherwise it stays dim.
//   ceiling ≤ 200 ft → CAT II lit
//   ceiling ≤ 100 ft → CAT II + CAT III lit
function catBadges(cat, ceilingHundreds) {
    if (!cat || cat < 2) return '';
    const reqCat = requiredCat(ceilingHundreds);
    const parts = [];
    if (cat >= 2) {
        const lit = reqCat >= 2;
        parts.push(`<span class="cat-badge cat-ii ${lit ? '' : 'inactive'}">CAT II</span>`);
    }
    if (cat >= 3) {
        const lit = reqCat >= 3;
        parts.push(`<span class="cat-badge cat-iii ${lit ? '' : 'inactive'}">CAT III</span>`);
    }
    return parts.join('');
}

function hwClass(hw) {
    if (hw >= 5) return 'headwind';
    if (hw >= 0) return 'light-headwind';
    if (hw > -5) return 'tailwind-mild';
    return 'tailwind-strong';
}

function xwClass(xwAbs) {
    if (xwAbs <= 12) return 'crosswind-light';
    if (xwAbs <= 15) return 'crosswind-moderate';
    return 'crosswind-strong';
}

function ceilingVisText(st) {
    const parts = [];
    if (st.ceilingHundreds !== null) {
        const low = st.ceilingHundreds < 10;
        const cls = low ? 'ceiling-vis-inline-warning' : 'ceiling-vis-inline';
        parts.push(`<span class="${cls}">CIG: ${st.ceilingHundreds} ${st.ceilingType}</span>`);
    }
    if (st.visibility) {
        parts.push(`<span class="ceiling-vis-inline-warning">VIS: ${st.visibility}</span>`);
    }
    return parts.join(' • ');
}

function renderCardInner(icao) {
    const st = aptState[icao];
    if (!st) return `<div class="airport-header"><div class="airport-code">${icao}</div></div><div style="padding:10px;color:var(--text-dim)">No data</div>`;

    const flightRulesClass = (st.rules || '').toLowerCase();
    const cigVis = ceilingVisText(st);
    const reqCat = requiredCat(st.ceilingHundreds);

    if (st.noRunway) {
        return `
            <div class="airport-header">
                <div class="airport-code">${icao}</div>
                <div class="flight-rules ${flightRulesClass}">${st.rules}</div>
            </div>
            <div class="wind-info">
                <div class="wind-direction">${st.windDir}°M/${st.windSpd}</div>
                <div class="altimeter">${st.altimeter}</div>
                ${cigVis}
            </div>
            <div style="padding: 15px; text-align: center; color: var(--text-dim); font-style: italic;">
                No runway data available for this airport
            </div>
            <div class="metar-section">
                <div class="metar-text">${st.metar}</div>
            </div>
        `;
    }

    // Group runways into reciprocal pairs, stacked: row1 = low-numbered end,
    // row2 = reciprocal directly below (visibility-hidden placeholder if none).
    const allRwys = Object.entries(st.runways).sort((a, b) => parseInt(a[0]) - parseInt(b[0]));
    const row1ids = [], row2ids = [];
    const used = new Set();
    for (const [id] of allRwys) {
        if (used.has(id)) continue;
        const rid = reciprocalIdent(id);
        if (rid && st.runways[rid] && !used.has(rid)) {
            const n1 = parseInt(id), n2 = parseInt(rid);
            if (n1 <= n2) { row1ids.push(id); row2ids.push(rid); }
            else          { row1ids.push(rid); row2ids.push(id); }
            used.add(id); used.add(rid);
        } else {
            row1ids.push(id);
            row2ids.push(null);
            used.add(id);
        }
    }

    function renderRwy(ident, r) {
        const unavailCls = r.avail ? '' : 'unavailable';
        const hwArrow = r.hw >= 0 ? '↓' : '↑';
        const hwAbs = Math.abs(r.hw);
        const xwArrow = r.xw > 0 ? '→' : r.xw < 0 ? '←' : '·';
        const cat = catBadges(r.cat, st.ceilingHundreds);
        // LAHSO capability badge: dimmed whenever this runway is LAHSO-capable,
        // lit when actually in effect (flagged by flagLahsoFromTopology).
        const lahsoSpec = runways[icao]?.lahso;
        const lahsoCapable = lahsoSpec && lahsoSpec[ident];
        const lahso = lahsoCapable
            ? `<span class="lahso-badge ${r.lahso ? '' : 'inactive'}" title="LAHSO hold-short capable (targets: ${lahsoSpec[ident].join(', ')})">LAHSO</span>`
            : '';
        const isPref = runways[icao]?.preferred === ident;
        const prefStar = isPref ? '<span class="preferred-mark" title="Preferred runway">★</span>' : '';
        const tooltip = !r.avail
            ? `UNAVAILABLE: ${r.unavailReason}`
            : r.noArr
                ? `${ident} ${r.hdg}°M — ${r.noArrReason}`
                : `${ident} ${r.hdg}°M — click to toggle role`;
        const onclick = r.avail ? `onclick="toggleRwy('${icao}','${ident}')"` : '';
        return `
            <div class="runway-item ${unavailCls}" ${onclick} title="${tooltip}">
                <div class="runway-number">
                    ${ident}${prefStar}${roleBadge(r.role)}${cat}${lahso}
                </div>
                <div class="wind-components">
                    <div class="wind-component ${hwClass(r.hw)}">
                        <span class="arrow">${hwArrow}</span>
                        <span>${hwAbs}</span>
                    </div>
                    <div class="wind-component ${xwClass(r.crosswindAbs)}">
                        <span class="arrow">${xwArrow}</span>
                        <span>${r.crosswindAbs}</span>
                    </div>
                </div>
            </div>
        `;
    }

    const row1 = row1ids.map(id => renderRwy(id, st.runways[id])).join('');
    const row2 = row2ids.map(id => id
        ? renderRwy(id, st.runways[id])
        : '<div class="runway-item" style="visibility:hidden"></div>'
    ).join('');
    const runwaysHTML = `<div class="rwy-row">${row1}</div><div class="rwy-row">${row2}</div>`;

    const wetBadge = st.wet
        ? '<span class="surface-badge wet">WET</span>'
        : '<span class="surface-badge dry">DRY</span>';
    const catWarn = reqCat > 1 ? `<span class="cat-required">CAT ${reqCat} required</span>` : '';

    // Rate box — show AAR/ADR from selected config if any
    let rateBox = '';
    if (st.arrRate !== null && st.arrRate !== undefined) {
        const total = st.arrRate + st.depRate;
        rateBox = `
            <div class="rate-box">
                <div class="rate-stack">
                    <div class="rate-row rate-arr"><span class="rate-label">AAR</span><span class="rate-num">${st.arrRate}</span></div>
                    <div class="rate-row rate-dep"><span class="rate-label">ADR</span><span class="rate-num">${st.depRate}</span></div>
                </div>
                <div class="rate-total"><div class="rate-num">${total}</div><div class="rate-label">mvts/hr</div></div>
            </div>
        `;
    }

    return `
        <div class="airport-header">
            <div class="airport-code">${icao}</div>
            <div class="flight-rules ${flightRulesClass}">${st.rules}</div>
            ${wetBadge}
            <button class="propose-btn" onclick="proposeAuto('${icao}')">Auto</button>
        </div>
        <div class="wind-info">
            <div class="wind-direction">${st.windDir}°M/${st.windSpd}</div>
            <div class="altimeter">${st.altimeter}</div>
            ${cigVis}
        </div>
        ${st.configName ? `<div class="config-name">${st.configName}${catWarn ? ' · ' + catWarn : ''}</div>` : ''}
        <div class="runways-grid">
            ${runwaysHTML}
        </div>
        ${rateBox}
        <div class="metar-section">
            <div class="metar-text">${st.metar}</div>
        </div>
    `;
}

function createErrorCard(airportCode, errorMessage) {
    const card = document.createElement('div');
    card.className = 'error-card';
    card.innerHTML = `<h3>${airportCode}</h3><p>Error: ${errorMessage}</p>`;
    return card;
}

function sanitizeMETAR(raw) {
    if (!raw) return '';
    const altimeterPattern = /(A\d{4})/;
    const match = raw.match(altimeterPattern);
    return match ? raw.split(match[0])[0] + match[0] : raw;
}
