// Premier League Analytics - Professional JavaScript

const TEAMS = [
    'Arsenal', 'Bournemouth', 'Tottenham', 'Sunderland',
    'Man City', 'Man United', 'Liverpool', 'Aston Villa',
    'Chelsea', 'Crystal Palace', 'Brentford', 'Newcastle',
    'Brighton', 'Everton', 'Leeds', 'Burnley',
    'Fulham', "Nott'm Forest", 'West Ham', 'Wolves'
];

// State management
const state = {
    currentTab: 'value',
    selectedTeam: null,
    selectedSeasons: 10,
    currentPeriod: {
        goalsScored: 'full',
        goalsConceded: 'full',
        corners: 'full'
    },
    charts: {
        goalsScored: null,
        goalsConceded: null,
        corners: null
    },
    summariesLoaded: false,
    dataLoaded: false,
    oddsLoaded: false,
    valueBetsLoaded: false,
    allValueBets: [],
    filteredValueBets: [],
    currentFilter: 'all',
    currentSort: 'ev-desc',
    minEV: -50,
    currentRegion: 'both',
    currentAIModel: 'complex',
    currentDateFilter: 'all',
    oddsMarketFilter: 'all',
    oddsRegionFilter: 'both',
    selectedMatchId: 'all',
    allOddsData: [],
    tableLoaded: false,
    summaryYears: 10
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    setupTeamSelection();
    setupPeriodFilters();
    setupSeasonFilter();
    setupEventListeners();
    
    // Load team summaries when tab is clicked
    document.querySelector('[data-tab="summary"]').addEventListener('click', () => {
        if (!state.summariesLoaded) {
            loadTeamSummaries();
            state.summariesLoaded = true;
        }
    });
    
    // Load live odds when tab is clicked
    document.querySelector('[data-tab="odds"]').addEventListener('click', () => {
        if (!state.oddsLoaded) {
            loadLiveOdds();
            state.oddsLoaded = true;
        }
    });
    
    // Load value bets immediately on page load
    loadValueBets();
    
    // Setup value bets filters
    setupValueBetsFilters();
    
    // Load PL Table when tab is clicked
    document.querySelector('[data-tab="table"]').addEventListener('click', () => {
        if (!state.tableLoaded) {
            loadPremierLeagueTable();
            state.tableLoaded = true;
        }
    });
    
    // Setup summary period filter
    const summaryPeriodFilter = document.getElementById('summary-period-filter');
    if (summaryPeriodFilter) {
        summaryPeriodFilter.addEventListener('change', (e) => {
            state.summaryYears = parseInt(e.target.value);
            loadTeamSummaries();
        });
    }
});

// Tab switching
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            
            // Update buttons
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update content
            tabContents.forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            state.currentTab = tabName;
        });
    });
}

// Team Selection
function setupTeamSelection() {
    const teamOptions = document.querySelectorAll('.team-option');
    
    teamOptions.forEach(option => {
        option.addEventListener('click', () => {
            const team = option.dataset.team;
            
            // Update active state
            teamOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');
            
            // Load team data
            state.selectedTeam = team;
            loadTeamAnalytics(team);
            
            // Show charts container
            document.getElementById('charts-container').classList.add('active');
        });
    });
}

// Period Filters
function setupPeriodFilters() {
    const periodButtons = document.querySelectorAll('.period-btn');
    
    periodButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const chartType = btn.dataset.chart;
            const period = btn.dataset.period;
            
            // Update active state within the same chart group
            const siblings = btn.parentElement.querySelectorAll('.period-btn');
            siblings.forEach(sib => sib.classList.remove('active'));
            btn.classList.add('active');
            
            // Update state
            if (chartType === 'goals-scored') {
                state.currentPeriod.goalsScored = period;
            } else if (chartType === 'goals-conceded') {
                state.currentPeriod.goalsConceded = period;
            } else if (chartType === 'corners') {
                state.currentPeriod.corners = period;
            }
            
            // Reload data for this chart
            if (state.selectedTeam) {
                loadTeamAnalytics(state.selectedTeam);
            }
        });
    });
}

// Season Filter
function setupSeasonFilter() {
    const seasonFilter = document.getElementById('season-filter');
    
    if (seasonFilter) {
        seasonFilter.addEventListener('change', (e) => {
            state.selectedSeasons = parseInt(e.target.value);
            
            // Reload data if a team is selected
            if (state.selectedTeam) {
                loadTeamAnalytics(state.selectedTeam);
            }
        });
    }
}

// Load Team Analytics
async function loadTeamAnalytics(team) {
    try {
        // Load data for each period with season filter
        const goalsScoredData = await fetch(`/api/team-cdf/${encodeURIComponent(team)}?period=${state.currentPeriod.goalsScored}&years=${state.selectedSeasons}`).then(r => r.json());
        const goalsConcededData = await fetch(`/api/team-cdf/${encodeURIComponent(team)}?period=${state.currentPeriod.goalsConceded}&years=${state.selectedSeasons}`).then(r => r.json());
        const cornersData = await fetch(`/api/team-cdf/${encodeURIComponent(team)}?period=${state.currentPeriod.corners}&years=${state.selectedSeasons}`).then(r => r.json());
        
        // Update charts
        updateChart('goalsScored', goalsScoredData.goals_scored_cdf, team, state.currentPeriod.goalsScored);
        updateChart('goalsConceded', goalsConcededData.goals_conceded_cdf, team, state.currentPeriod.goalsConceded);
        updateChart('corners', cornersData.corners_cdf, team, state.currentPeriod.corners);
        
    } catch (error) {
        console.error('Error loading team analytics:', error);
    }
}

// Update Chart
function updateChart(chartType, cdfData, team, period) {
    const chartId = chartType === 'goalsScored' ? 'goals-scored-chart' : 
                    chartType === 'goalsConceded' ? 'goals-conceded-chart' : 
                    'corners-chart';
    
    const ctx = document.getElementById(chartId).getContext('2d');
    
    // Destroy existing chart
    if (state.charts[chartType]) {
        state.charts[chartType].destroy();
    }
    
    // Prepare data
    const labels = cdfData.map(d => d.value);
    const probabilities = cdfData.map(d => (d.probability * 100).toFixed(1));
    
    // Chart configuration
    const config = {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Cumulative Probability (%)',
                data: probabilities,
                borderColor: '#003d71',
                backgroundColor: 'rgba(0, 61, 113, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.1,
                pointRadius: 4,
                pointBackgroundColor: '#003d71',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            family: 'Inter',
                            size: 12,
                            weight: '500'
                        },
                        color: '#495057'
                    }
                },
                title: {
                    display: true,
                    text: `${team} - ${getPeriodLabel(period)}`,
                    font: {
                        family: 'Inter',
                        size: 14,
                        weight: '600'
                    },
                    color: '#212529'
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: {
                        family: 'Inter',
                        size: 13,
                        weight: '600'
                    },
                    bodyFont: {
                        family: 'Inter',
                        size: 12
                    },
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            return `Probability: ${context.parsed.y}%`;
                        },
                        afterLabel: function(context) {
                            const value = context.label;
                            const prob = context.parsed.y;
                            return `P(X ≤ ${value}) = ${prob}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: getXAxisLabel(chartType),
                        font: {
                            family: 'Inter',
                            size: 12,
                            weight: '600'
                        },
                        color: '#495057'
                    },
                    grid: {
                        color: '#e9ecef',
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            family: 'Inter',
                            size: 11
                        },
                        color: '#6c757d'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Cumulative Probability (%)',
                        font: {
                            family: 'Inter',
                            size: 12,
                            weight: '600'
                        },
                        color: '#495057'
                    },
                    min: 0,
                    max: 100,
                    grid: {
                        color: '#e9ecef',
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            family: 'Inter',
                            size: 11
                        },
                        color: '#6c757d',
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    };
    
    // Create new chart
    state.charts[chartType] = new Chart(ctx, config);
}

// Helper functions
function getPeriodLabel(period) {
    switch(period) {
        case 'first_half': return '1st Half';
        case 'second_half': return '2nd Half';
        default: return 'Full Match';
    }
}

function getXAxisLabel(chartType) {
    switch(chartType) {
        case 'goalsScored': return 'Goals Scored';
        case 'goalsConceded': return 'Goals Conceded';
        case 'corners': return 'Corners';
        default: return 'Value';
    }
}

// Setup event listeners
function setupEventListeners() {
    // Additional event listeners can be added here
}

// Load Premier League Table
async function loadPremierLeagueTable() {
    const loadingEl = document.getElementById('table-loading');
    const tableEl = document.getElementById('pl-table-content');
    
    loadingEl.style.display = 'flex';
    
    try {
        const response = await fetch('/api/premier-league-table');
        const table = await response.json();
        
        loadingEl.style.display = 'none';
        renderPremierLeagueTable(table);
    } catch (error) {
        console.error('Error loading PL table:', error);
        loadingEl.style.display = 'none';
        tableEl.innerHTML = '<div class="error-message"><p>Unable to load table.</p></div>';
    }
}

// Render Premier League Table
function renderPremierLeagueTable(table) {
    const tableEl = document.getElementById('pl-table-content');
    
    if (table.length === 0) {
        tableEl.innerHTML = '<p class="text-center">No data available.</p>';
        return;
    }
    
    const html = `
        <div style="margin-bottom: 1rem; padding: 1rem; background-color: #f0f9ff; border-left: 3px solid var(--accent-blue); border-radius: var(--radius-md);">
            <p style="font-size: 0.875rem; color: var(--gray-700); margin: 0;">
                <strong>Note:</strong> Established teams show stats from last 38 games. 
                Newly promoted teams (marked with *) show current season stats only.
            </p>
        </div>
        <div class="summary-table">
            <table>
                <thead>
                    <tr>
                        <th>Pos</th>
                        <th>Team</th>
                        <th>P</th>
                        <th>W%</th>
                        <th>D%</th>
                        <th>L%</th>
                        <th>GF</th>
                        <th>GA</th>
                        <th>GD</th>
                        <th>Pts</th>
                    </tr>
                </thead>
                <tbody>
                    ${table.map((team, index) => `
                        <tr>
                            <td style="font-weight: 700; color: var(--primary-blue);">${index + 1}</td>
                            <td class="team-name-cell">
                                ${team.team}${team.is_promoted ? ' <span style="color: var(--accent-blue);">*</span>' : ''}
                            </td>
                            <td>${team.played}</td>
                            <td class="stat-positive">${team.win_pct}%</td>
                            <td class="stat-neutral">${team.draw_pct}%</td>
                            <td class="stat-negative">${team.loss_pct}%</td>
                            <td>${team.goals_for}</td>
                            <td>${team.goals_against}</td>
                            <td class="${team.goal_difference > 0 ? 'stat-positive' : team.goal_difference < 0 ? 'stat-negative' : 'stat-neutral'}">
                                ${team.goal_difference > 0 ? '+' : ''}${team.goal_difference}
                            </td>
                            <td style="font-weight: 700; color: var(--primary-blue);">${team.points}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    tableEl.innerHTML = html;
}

// Load team summaries
async function loadTeamSummaries() {
    const loadingEl = document.getElementById('summary-loading');
    const tableEl = document.getElementById('team-summaries-table');
    
    loadingEl.style.display = 'flex';
    
    try {
        const response = await fetch(`/api/team-summaries?years=${state.summaryYears}`);
        const summaries = await response.json();
        
        loadingEl.style.display = 'none';
        renderTeamSummaries(summaries);
    } catch (error) {
        console.error('Error loading team summaries:', error);
        loadingEl.style.display = 'none';
        tableEl.innerHTML = '<div class="error-message"><p>Unable to load team summaries.</p></div>';
    }
}

// Render team summaries table
function renderTeamSummaries(summaries) {
    const tableEl = document.getElementById('team-summaries-table');
    
    if (summaries.length === 0) {
        tableEl.innerHTML = '<p class="text-center">No data available.</p>';
        return;
    }
    
    const html = `
        <div class="summary-table">
            <table>
                <thead>
                    <tr>
                        <th>Team</th>
                        <th>Matches</th>
                        <th>Goals Scored</th>
                        <th>Goals Conceded</th>
                        <th>Goal Diff</th>
                        <th>Corners For</th>
                        <th>Corners Against</th>
                    </tr>
                </thead>
                <tbody>
                    ${summaries.map(team => `
                        <tr>
                            <td class="team-name-cell">${team.team}</td>
                            <td>${team.matches_played}</td>
                            <td class="stat-positive">${team.avg_goals_scored}</td>
                            <td class="stat-negative">${team.avg_goals_conceded}</td>
                            <td class="${team.goal_difference > 0 ? 'stat-positive' : team.goal_difference < 0 ? 'stat-negative' : 'stat-neutral'}">
                                ${team.goal_difference > 0 ? '+' : ''}${team.goal_difference}
                            </td>
                            <td>${team.avg_corners_for}</td>
                            <td>${team.avg_corners_against}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    tableEl.innerHTML = html;
}

// Load comprehensive data summary
async function loadDataSummary() {
    const loadingEl = document.getElementById('data-loading');
    const contentEl = document.getElementById('data-summary-content');
    
    loadingEl.style.display = 'flex';
    
    try {
        const response = await fetch('/api/data-summary');
        const data = await response.json();
        
        loadingEl.style.display = 'none';
        renderDataSummary(data);
    } catch (error) {
        console.error('Error loading data summary:', error);
        loadingEl.style.display = 'none';
        contentEl.innerHTML = '<div class="error-message"><p>Unable to load data summary.</p></div>';
    }
}

// Render comprehensive data summary (simplified for professional look)
function renderDataSummary(data) {
    const contentEl = document.getElementById('data-summary-content');
    
    const html = `
        <div class="card">
            <h3 style="color: var(--primary-blue); margin-bottom: 1.5rem;">Dataset Overview</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 2rem; margin-bottom: 2rem;">
                <div>
                    <div style="font-size: 2rem; font-weight: 600; color: var(--primary-blue);">${data.overall.total_matches.toLocaleString()}</div>
                    <div style="color: var(--gray-600); margin-top: 0.25rem;">Total Matches</div>
                </div>
                <div>
                    <div style="font-size: 2rem; font-weight: 600; color: var(--primary-blue);">${data.overall.total_seasons}</div>
                    <div style="color: var(--gray-600); margin-top: 0.25rem;">Seasons</div>
                </div>
                <div>
                    <div style="font-size: 2rem; font-weight: 600; color: var(--primary-blue);">${data.overall.total_teams}</div>
                    <div style="color: var(--gray-600); margin-top: 0.25rem;">Teams</div>
                </div>
                <div>
                    <div style="font-size: 2rem; font-weight: 600; color: var(--primary-blue);">${parseFloat(data.overall.avg_goals_per_match).toFixed(2)}</div>
                    <div style="color: var(--gray-600); margin-top: 0.25rem;">Avg Goals/Match</div>
                </div>
            </div>
            <div style="padding-top: 1rem; border-top: 1px solid var(--gray-200); color: var(--gray-600); font-size: 0.875rem;">
                <strong>Data Source:</strong> football-data.co.uk | <strong>Range:</strong> ${data.overall.earliest_match} to ${data.overall.latest_match}
            </div>
        </div>
        
        <div class="card">
            <h3 style="color: var(--primary-blue); margin-bottom: 1.5rem;">Home vs Away Statistics</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 2rem;">
                <div>
                    <div style="font-size: 1.5rem; font-weight: 600; color: var(--success);">${data.home_away_stats.home_win_percentage}%</div>
                    <div style="color: var(--gray-600); margin-top: 0.25rem;">Home Wins</div>
                </div>
                <div>
                    <div style="font-size: 1.5rem; font-weight: 600; color: var(--gray-700);">${data.home_away_stats.draw_percentage}%</div>
                    <div style="color: var(--gray-600); margin-top: 0.25rem;">Draws</div>
                </div>
                <div>
                    <div style="font-size: 1.5rem; font-weight: 600; color: var(--info);">${data.home_away_stats.away_win_percentage}%</div>
                    <div style="color: var(--gray-600); margin-top: 0.25rem;">Away Wins</div>
                </div>
            </div>
        </div>
    `;
    
    contentEl.innerHTML = html;
}

// Load live odds
async function loadLiveOdds() {
    const loadingEl = document.getElementById('odds-loading');
    const contentEl = document.getElementById('odds-content');
    const timestampEl = document.getElementById('odds-timestamp');
    
    loadingEl.style.display = 'flex';
    
    try {
        const response = await fetch('/api/live-odds');
        const data = await response.json();
        
        if (data.error) {
            loadingEl.style.display = 'none';
            contentEl.innerHTML = '<div class="error-message"><p>' + data.error + '</p></div>';
            return;
        }
        
        loadingEl.style.display = 'none';
        state.allOddsData = data.matches || [];
        
        // Populate match selector
        populateMatchSelector(state.allOddsData);
        
        renderLiveOdds(state.allOddsData);
        
        // Update timestamp
        const lastUpdated = new Date(data.last_updated);
        timestampEl.innerHTML = `<p>Last updated: ${lastUpdated.toLocaleString()}</p>`;
        
    } catch (error) {
        console.error('Error loading live odds:', error);
        loadingEl.style.display = 'none';
        contentEl.innerHTML = '<div class="error-message"><p>Unable to load live odds. Please try again later.</p></div>';
    }
}

// Populate match selector dropdown
function populateMatchSelector(matches) {
    const matchSelector = document.getElementById('match-selector');
    if (!matchSelector) return;
    
    // Clear existing options except "All Matches"
    matchSelector.innerHTML = '<option value="all">All Matches</option>';
    
    matches.forEach((match, index) => {
        const matchTime = new Date(match.commence_time);
        const matchTimeStr = matchTime.toLocaleString('en-GB', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        const option = document.createElement('option');
        option.value = index;
        option.textContent = `${match.home_team} vs ${match.away_team} - ${matchTimeStr}`;
        matchSelector.appendChild(option);
    });
}

// Render live odds
function renderLiveOdds(matches) {
    const contentEl = document.getElementById('odds-content');
    
    if (!matches || matches.length === 0) {
        contentEl.innerHTML = '<div class="card"><p class="text-center">No upcoming Premier League matches available at this time.</p></div>';
        return;
    }
    
    // Filter matches based on selection
    let filteredMatches = matches;
    if (state.selectedMatchId !== 'all') {
        const matchIndex = parseInt(state.selectedMatchId);
        filteredMatches = [matches[matchIndex]];
    }
    
    let html = '';
    
    filteredMatches.forEach(match => {
        const matchTime = new Date(match.commence_time);
        const matchTimeStr = matchTime.toLocaleString('en-GB', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        // Filter bookmakers by region
        let uk_bookmakers = match.uk_bookmakers || [];
        let us_bookmakers = match.us_bookmakers || [];
        
        if (state.oddsRegionFilter === 'uk') {
            us_bookmakers = [];
        } else if (state.oddsRegionFilter === 'us') {
            uk_bookmakers = [];
        }
        
        html += `
            <div class="odds-card">
                <div class="odds-header">
                    <div class="match-info">
                        <h3>${match.home_team} vs ${match.away_team}</h3>
                        <p class="match-time">${matchTimeStr}</p>
                    </div>
                </div>
                
                ${uk_bookmakers.length > 0 ? `
                <div class="bookmaker-section">
                    <h4 class="region-title">🇬🇧 UK Bookmakers</h4>
                    ${renderBookmakerOdds(match.home_team, match.away_team, uk_bookmakers)}
                </div>
                ` : ''}
                
                ${us_bookmakers.length > 0 ? `
                <div class="bookmaker-section">
                    <h4 class="region-title">🇺🇸 US Bookmakers</h4>
                    ${renderBookmakerOdds(match.home_team, match.away_team, us_bookmakers)}
                </div>
                ` : ''}
                
                ${uk_bookmakers.length === 0 && us_bookmakers.length === 0 ? `
                <p class="text-center" style="color: var(--gray-600);">No odds available for this match with the selected filters.</p>
                ` : ''}
            </div>
        `;
    });
    
    contentEl.innerHTML = html;
}

// Render bookmaker odds table
function renderBookmakerOdds(homeTeam, awayTeam, bookmakers) {
    if (bookmakers.length === 0) {
        return '<p class="text-center">No bookmakers available</p>';
    }
    
    let html = '';
    
    // Render Moneyline (h2h) if selected
    if (state.oddsMarketFilter === 'all' || state.oddsMarketFilter === 'h2h') {
        html += renderMoneylineTable(homeTeam, awayTeam, bookmakers);
    }
    
    // Render Goals (totals) if selected
    if (state.oddsMarketFilter === 'all' || state.oddsMarketFilter === 'totals') {
        html += renderGoalsTable(bookmakers);
    }
    
    // Render Corners if selected
    if (state.oddsMarketFilter === 'all' || state.oddsMarketFilter === 'corners') {
        html += renderCornersTable(bookmakers);
    }
    
    return html;
}

// Render moneyline table
function renderMoneylineTable(homeTeam, awayTeam, bookmakers) {
    // Find best odds for each outcome
    let bestHomeOdds = 0;
    let bestDrawOdds = 0;
    let bestAwayOdds = 0;
    
    bookmakers.forEach(bm => {
        if (bm.h2h[homeTeam] && bm.h2h[homeTeam] > bestHomeOdds) {
            bestHomeOdds = bm.h2h[homeTeam];
        }
        if (bm.h2h['Draw'] && bm.h2h['Draw'] > bestDrawOdds) {
            bestDrawOdds = bm.h2h['Draw'];
        }
        if (bm.h2h[awayTeam] && bm.h2h[awayTeam] > bestAwayOdds) {
            bestAwayOdds = bm.h2h[awayTeam];
        }
    });
    
    let html = `
        <div style="margin-bottom: 1.5rem;">
            <h5 style="color: var(--gray-700); font-size: 0.9375rem; font-weight: 600; margin-bottom: 0.75rem;">Match Winner (Moneyline)</h5>
            <div class="odds-table-container">
                <table class="odds-table">
                    <thead>
                        <tr>
                            <th>Bookmaker</th>
                            <th>${homeTeam}</th>
                            <th>Draw</th>
                            <th>${awayTeam}</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    bookmakers.forEach(bm => {
        const homeOdds = bm.h2h[homeTeam] || '-';
        const drawOdds = bm.h2h['Draw'] || '-';
        const awayOdds = bm.h2h[awayTeam] || '-';
        
        const homeClass = homeOdds === bestHomeOdds && homeOdds !== '-' ? 'best-odds' : '';
        const drawClass = drawOdds === bestDrawOdds && drawOdds !== '-' ? 'best-odds' : '';
        const awayClass = awayOdds === bestAwayOdds && awayOdds !== '-' ? 'best-odds' : '';
        
        html += `
            <tr>
                <td class="bookmaker-name">${bm.name}</td>
                <td class="${homeClass}">${homeOdds !== '-' ? homeOdds.toFixed(2) : '-'}</td>
                <td class="${drawClass}">${drawOdds !== '-' ? drawOdds.toFixed(2) : '-'}</td>
                <td class="${awayClass}">${awayOdds !== '-' ? awayOdds.toFixed(2) : '-'}</td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    return html;
}

// Render goals table
function renderGoalsTable(bookmakers) {
    // Collect all unique totals lines
    const totalsLines = new Map();
    
    bookmakers.forEach(bm => {
        if (bm.totals) {
            Object.keys(bm.totals).forEach(key => {
                const { point, price } = bm.totals[key];
                const lineKey = `${key}_${point}`;
                if (!totalsLines.has(lineKey)) {
                    totalsLines.set(lineKey, { name: key, point, bookmakers: {} });
                }
                if (!totalsLines.get(lineKey).bookmakers[bm.name] || price > totalsLines.get(lineKey).bookmakers[bm.name]) {
                    totalsLines.get(lineKey).bookmakers[bm.name] = price;
                }
            });
        }
    });
    
    if (totalsLines.size === 0) {
        return '';
    }
    
    let html = `
        <div style="margin-bottom: 1.5rem;">
            <h5 style="color: var(--gray-700); font-size: 0.9375rem; font-weight: 600; margin-bottom: 0.75rem;">Total Goals (Over/Under)</h5>
            <div class="odds-table-container">
                <table class="odds-table">
                    <thead>
                        <tr>
                            <th>Bookmaker</th>
    `;
    
    // Get unique lines for headers
    const uniqueLines = Array.from(totalsLines.values());
    uniqueLines.forEach(line => {
        html += `<th>${line.name.charAt(0).toUpperCase() + line.name.slice(1)} ${line.point}</th>`;
    });
    
    html += `
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    // Render each bookmaker's odds
    bookmakers.forEach(bm => {
        html += `<tr><td class="bookmaker-name">${bm.name}</td>`;
        
        uniqueLines.forEach(line => {
            const lineKey = `${line.name}_${line.point}`;
            const odds = line.bookmakers[bm.name];
            html += `<td>${odds ? odds.toFixed(2) : '-'}</td>`;
        });
        
        html += `</tr>`;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    return html;
}

// Render corners table
function renderCornersTable(bookmakers) {
    // Note: The Odds API doesn't typically provide corners markets
    // This is a placeholder that will show if data becomes available
    
    // Check if any bookmaker has corners data
    const hasCornersData = bookmakers.some(bm => bm.corners && Object.keys(bm.corners).length > 0);
    
    if (!hasCornersData) {
        return `
            <div style="margin-bottom: 1.5rem;">
                <h5 style="color: var(--gray-700); font-size: 0.9375rem; font-weight: 600; margin-bottom: 0.75rem;">Corners (Over/Under)</h5>
                <div style="padding: 1.5rem; background-color: var(--gray-50); border-radius: var(--radius-md); text-align: center; color: var(--gray-600);">
                    <p>Corners markets not available from current bookmakers</p>
                    <p style="font-size: 0.875rem; margin-top: 0.5rem;">This market may not be offered by all bookmakers in the API</p>
                </div>
            </div>
        `;
    }
    
    // If corners data exists, render it similar to goals
    const cornersLines = new Map();
    
    bookmakers.forEach(bm => {
        if (bm.corners) {
            Object.keys(bm.corners).forEach(key => {
                const { point, price } = bm.corners[key];
                const lineKey = `${key}_${point}`;
                if (!cornersLines.has(lineKey)) {
                    cornersLines.set(lineKey, { name: key, point, bookmakers: {} });
                }
                if (!cornersLines.get(lineKey).bookmakers[bm.name] || price > cornersLines.get(lineKey).bookmakers[bm.name]) {
                    cornersLines.get(lineKey).bookmakers[bm.name] = price;
                }
            });
        }
    });
    
    let html = `
        <div style="margin-bottom: 1.5rem;">
            <h5 style="color: var(--gray-700); font-size: 0.9375rem; font-weight: 600; margin-bottom: 0.75rem;">Corners (Over/Under)</h5>
            <div class="odds-table-container">
                <table class="odds-table">
                    <thead>
                        <tr>
                            <th>Bookmaker</th>
    `;
    
    const uniqueLines = Array.from(cornersLines.values());
    uniqueLines.forEach(line => {
        html += `<th>${line.name.charAt(0).toUpperCase() + line.name.slice(1)} ${line.point}</th>`;
    });
    
    html += `
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    bookmakers.forEach(bm => {
        html += `<tr><td class="bookmaker-name">${bm.name}</td>`;
        
        uniqueLines.forEach(line => {
            const lineKey = `${line.name}_${line.point}`;
            const odds = line.bookmakers[bm.name];
            html += `<td>${odds ? odds.toFixed(2) : '-'}</td>`;
        });
        
        html += `</tr>`;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    return html;
}

// Load value bets
async function loadValueBets() {
    const loadingEl = document.getElementById('value-loading');
    const containerEl = document.getElementById('value-bets-container');
    const timestampEl = document.getElementById('value-timestamp');
    
    loadingEl.style.display = 'flex';
    
    try {
        const response = await fetch(`/api/value-bets?region=${state.currentRegion}&model=${state.currentAIModel}`);
        const data = await response.json();
        
        if (data.error) {
            loadingEl.style.display = 'none';
            containerEl.innerHTML = '<div class="error-message"><p>' + data.error + '</p></div>';
            return;
        }
        
        loadingEl.style.display = 'none';
        state.allValueBets = data.value_bets || [];
        state.valueBetsLoaded = true;
        
        // Apply initial filters and render
        filterAndRenderValueBets();
        
        // Update timestamp
        const lastUpdated = new Date(data.last_updated);
        timestampEl.innerHTML = `<p>Last updated: ${lastUpdated.toLocaleString()}</p>`;
        
    } catch (error) {
        console.error('Error loading value bets:', error);
        loadingEl.style.display = 'none';
        containerEl.innerHTML = '<div class="error-message"><p>Unable to load value bets. Please try again later.</p></div>';
    }
}

// Setup value bets filters
function setupValueBetsFilters() {
    // Type filter chips
    const filterChips = document.querySelectorAll('.filter-chip:not(.region-chip)');
    filterChips.forEach(chip => {
        if (!chip.classList.contains('region-chip') && !chip.classList.contains('market-chip') && !chip.classList.contains('odds-region-chip')) {
            chip.addEventListener('click', () => {
                filterChips.forEach(c => {
                    if (!c.classList.contains('region-chip') && !c.classList.contains('market-chip') && !c.classList.contains('odds-region-chip')) {
                        c.classList.remove('active');
                    }
                });
                chip.classList.add('active');
                state.currentFilter = chip.dataset.filter;
                filterAndRenderValueBets();
            });
        }
    });
    
    // Region chips
    const regionChips = document.querySelectorAll('.region-chip');
    regionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            regionChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            state.currentRegion = chip.dataset.region;
            // Reload value bets with new region filter
            loadValueBets();
        });
    });
    
    // AI Model selector
    const modelSelector = document.getElementById('ai-model-selector');
    const modelDescription = document.getElementById('model-description');
    if (modelSelector && modelDescription) {
        modelSelector.addEventListener('change', (e) => {
            state.currentAIModel = e.target.value;
            
            // Update description based on selected model
            const descriptions = {
                'simple': 'Pure historical stats - Uses only this season\'s win/draw/loss rates and over/under frequencies',
                'opponent': 'Opponent-adjusted - Considers team strength based on goal difference and attacking/defensive metrics',
                'complex': 'Multi-factor AI - Uses historical data, home advantage factor, weighted recent form, and team strength metrics',
                'anomaly': 'Bookmaker Anomaly Detector - Finds bookmakers offering 25%+ better odds than the market average'
            };
            
            modelDescription.innerHTML = `<small>${descriptions[state.currentAIModel]}</small>`;
            
            // Reload value bets with new model
            loadValueBets();
        });
    }
    
    // Date filter
    const dateFilter = document.getElementById('date-filter');
    if (dateFilter) {
        dateFilter.addEventListener('change', (e) => {
            state.currentDateFilter = e.target.value;
            filterAndRenderValueBets();
        });
    }
    
    // Sort select
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            state.currentSort = e.target.value;
            filterAndRenderValueBets();
        });
    }
    
    // EV slider
    const evSlider = document.getElementById('ev-slider');
    const evValue = document.getElementById('ev-value');
    if (evSlider && evValue) {
        evSlider.addEventListener('input', (e) => {
            state.minEV = parseFloat(e.target.value);
            evValue.textContent = state.minEV + '%';
            filterAndRenderValueBets();
        });
    }
    
    // Setup odds market filters
    const marketChips = document.querySelectorAll('.market-chip');
    marketChips.forEach(chip => {
        chip.addEventListener('click', () => {
            marketChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            state.oddsMarketFilter = chip.dataset.market;
            renderLiveOdds(state.allOddsData);
        });
    });
    
    // Setup odds region filters
    const oddsRegionChips = document.querySelectorAll('.odds-region-chip');
    oddsRegionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            oddsRegionChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            state.oddsRegionFilter = chip.dataset.oddsRegion;
            renderLiveOdds(state.allOddsData);
        });
    });
    
    // Setup match selector
    const matchSelector = document.getElementById('match-selector');
    if (matchSelector) {
        matchSelector.addEventListener('change', (e) => {
            state.selectedMatchId = e.target.value;
            renderLiveOdds(state.allOddsData);
        });
    }
}

// Filter and render value bets
function filterAndRenderValueBets() {
    let filtered = [...state.allValueBets];
    
    // Apply date filter
    if (state.currentDateFilter !== 'all') {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000);
        const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
        
        filtered = filtered.filter(bet => {
            const matchDate = new Date(bet.commence_time);
            const matchDay = new Date(matchDate.getFullYear(), matchDate.getMonth(), matchDate.getDate());
            
            if (state.currentDateFilter === 'today') {
                return matchDay.getTime() === today.getTime();
            } else if (state.currentDateFilter === 'tomorrow') {
                return matchDay.getTime() === tomorrow.getTime();
            } else if (state.currentDateFilter === 'weekend') {
                const day = matchDay.getDay();
                return (day === 6 || day === 0) && matchDay >= today && matchDay < nextWeek;
            } else if (state.currentDateFilter === 'week') {
                return matchDay >= today && matchDay < nextWeek;
            }
            return true;
        });
    }
    
    // Apply type filter
    if (state.currentFilter !== 'all') {
        filtered = filtered.filter(bet => bet.bet_type === state.currentFilter);
    }
    
    // Apply min EV filter
    filtered = filtered.filter(bet => bet.ev >= state.minEV);
    
    // Apply sorting
    filtered.sort((a, b) => {
        switch (state.currentSort) {
            case 'ev-desc':
                return b.ev - a.ev;
            case 'ev-asc':
                return a.ev - b.ev;
            case 'odds-desc':
                return b.best_odds - a.best_odds;
            case 'odds-asc':
                return a.best_odds - b.best_odds;
            default:
                return b.ev - a.ev;
        }
    });
    
    state.filteredValueBets = filtered;
    
    // Update count
    document.getElementById('bet-count').textContent = filtered.length;
    document.getElementById('total-bets').textContent = state.allValueBets.length;
    
    // Render
    renderValueBets(filtered);
}

// Render value bets
function renderValueBets(bets) {
    const containerEl = document.getElementById('value-bets-container');
    
    if (!bets || bets.length === 0) {
        containerEl.innerHTML = `
            <div class="no-value-bets">
                <h3>No value bets found</h3>
                <p>Try adjusting your filters or check back later for new opportunities.</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    
    bets.forEach(bet => {
        const matchTime = new Date(bet.commence_time);
        const matchTimeStr = matchTime.toLocaleString('en-GB', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        // Calculate EV bar width (0-100 scale, only show for positive)
        const evWidth = bet.ev >= 0 ? Math.min(bet.ev, 100) : 0;
        const evBarClass = bet.ev >= 0 ? 'ev-bar-fill' : 'ev-bar-fill-negative';
        
        // Check if this is an anomaly bet
        const isAnomaly = bet.explanation && bet.explanation.includes('Anomaly detected');
        
        html += `
            <div class="value-bet-card ${isAnomaly ? 'anomaly-bet' : ''}">
                ${isAnomaly ? '<div class="anomaly-badge">🔥 ANOMALY</div>' : ''}
                <div class="bet-match-info">
                    <h3>${bet.match}</h3>
                    <div class="bet-market">${bet.bet_type} | ${bet.market}</div>
                    <div class="bet-time">${matchTimeStr}</div>
                    ${bet.explanation ? `<div class="bet-explanation"><em>${bet.explanation}</em></div>` : ''}
                </div>
                
                <div class="bet-stat-col">
                    <div class="stat-label">AI Probability</div>
                    <div class="stat-value ai-prob">${bet.ai_probability}%</div>
                </div>
                
                <div class="bet-stat-col">
                    <div class="stat-label">Implied Probability</div>
                    <div class="stat-value implied-prob">${bet.implied_probability}%</div>
                </div>
                
                <div class="bet-stat-col">
                    <div class="stat-label">EV</div>
                    <div class="stat-value ev-value-display ${bet.ev >= 0 ? 'positive' : 'negative'}">${bet.ev >= 0 ? '+' : ''}${bet.ev.toFixed(2)}%</div>
                    ${bet.ev >= 0 ? `
                    <div class="ev-bar">
                        <div class="${evBarClass}" style="width: ${evWidth}%"></div>
                    </div>
                    ` : '<div style="font-size: 0.75rem; color: var(--gray-500); margin-top: 0.25rem;">No value</div>'}
                </div>
                
                <div class="bet-odds-col">
                    <div class="stat-label">Best Odds</div>
                    <div class="odds-value">${bet.best_odds}</div>
                    <div class="bookmaker-badge">${bet.bookmaker}</div>
                </div>
            </div>
        `;
    });
    
    containerEl.innerHTML = html;
}



