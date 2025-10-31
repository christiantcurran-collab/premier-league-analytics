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
    currentTab: 'analytics',
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
    dataLoaded: false
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    setupTeamSelection();
    setupPeriodFilters();
    setupSeasonFilter();
    setupEventListeners();
    
    // Load data summary when tab is clicked
    document.querySelector('[data-tab="data"]').addEventListener('click', () => {
        if (!state.dataLoaded) {
            loadDataSummary();
            state.dataLoaded = true;
        }
    });
    
    // Load team summaries when tab is clicked
    document.querySelector('[data-tab="summary"]').addEventListener('click', () => {
        if (!state.summariesLoaded) {
            loadTeamSummaries();
            state.summariesLoaded = true;
        }
    });
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

// Load team summaries
async function loadTeamSummaries() {
    const loadingEl = document.getElementById('summary-loading');
    const tableEl = document.getElementById('team-summaries-table');
    
    loadingEl.style.display = 'flex';
    
    try {
        const response = await fetch('/api/team-summaries');
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







