class DashboardApp {
    constructor() {
        this.charts = {};
        this.colors = {
            cyan: '#00d4ff',
            purple: '#7c3aed',
            emerald: '#10b981',
            red: '#ef4444',
            yellow: '#fbbf24',
            bgCard: 'rgba(26, 26, 46, 0.8)',
            textPrimary: '#f8fafc',
            textSecondary: '#94a3b8',
            gridLines: 'rgba(255, 255, 255, 0.06)'
        };
        
        // Use demo data if API fails
        this.demoData = {
            kpis: {
                totalFailures: 1284,
                aiResolved: 842,
                resolvedPercent: 65,
                avgResolutionTime: 4.5, // minutes
                memoryHits: 312
            },
            failuresOverTime: {
                labels: Array.from({length: 30}, (_, i) => `Day ${i+1}`),
                data: Array.from({length: 30}, () => Math.floor(Math.random() * 50) + 10)
            },
            platformStats: [450, 320, 514],
            categories: {
                labels: ['DEPENDENCY_CONFLICT', 'TEST_FAILURE', 'LINT_ERROR', 'TIMEOUT', 'INFRA_ERROR'],
                data: [450, 320, 210, 180, 124]
            },
            fixSuccess: {
                labels: ['Accepted', 'Rejected', 'Pending'],
                data: [842, 120, 322]
            },
            recentFailures: [
                { id: 1, time: Date.now() - 300000, platform: 'GitHub Actions', job: 'build-ui', category: 'DEPENDENCY_CONFLICT', summary: 'React version mismatch in package-lock.json', status: 'resolved', confidence: 95 },
                { id: 2, time: Date.now() - 1200000, platform: 'Jenkins', job: 'api-deploy', category: 'INFRA_ERROR', summary: 'AWS credentials expired', status: 'pending', confidence: 60 },
                { id: 3, time: Date.now() - 3600000, platform: 'TeamCity', job: 'integration-tests', category: 'TEST_FAILURE', summary: 'Expected 200 OK, got 500 Internal Server Error', status: 'failed', confidence: 85 },
                { id: 4, time: Date.now() - 7200000, platform: 'GitHub Actions', job: 'lint', category: 'LINT_ERROR', summary: 'Missing trailing comma', status: 'resolved', confidence: 99 },
                { id: 5, time: Date.now() - 14400000, platform: 'Jenkins', job: 'docker-build', category: 'TIMEOUT', summary: 'Build exceeded 30m timeout', status: 'pending', confidence: 40 }
            ]
        };
    }

    init() {
        this.setupChartDefaults();
        this.initCharts();
        this.fetchStats();
        
        // Auto-refresh every 30 seconds
        setInterval(() => this.fetchStats(), 30000);
    }

    setupChartDefaults() {
        Chart.defaults.color = this.colors.textSecondary;
        Chart.defaults.font.family = "'Inter', sans-serif";
        Chart.defaults.scale.grid.color = this.colors.gridLines;
        Chart.defaults.plugins.tooltip.backgroundColor = this.colors.bgCard;
        Chart.defaults.plugins.tooltip.titleColor = this.colors.textPrimary;
        Chart.defaults.plugins.tooltip.padding = 10;
        Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.1)';
        Chart.defaults.plugins.tooltip.borderWidth = 1;
    }

    initCharts() {
        // Failures Over Time (Line Chart)
        const ctxTime = document.getElementById('failuresOverTimeChart').getContext('2d');
        const gradientTime = ctxTime.createLinearGradient(0, 0, 0, 300);
        gradientTime.addColorStop(0, 'rgba(0, 212, 255, 0.4)');
        gradientTime.addColorStop(1, 'rgba(0, 212, 255, 0.0)');

        this.charts.failuresOverTime = new Chart(ctxTime, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Failures',
                    data: [],
                    borderColor: this.colors.cyan,
                    backgroundColor: gradientTime,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.colors.cyan,
                    pointRadius: 0,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, border: { display: false } },
                    x: { border: { display: false }, grid: { display: false } }
                }
            }
        });

        // Platform (Doughnut Chart)
        const ctxPlatform = document.getElementById('platformChart').getContext('2d');
        this.charts.platform = new Chart(ctxPlatform, {
            type: 'doughnut',
            data: {
                labels: ['Jenkins', 'TeamCity', 'GitHub Actions'],
                datasets: [{
                    data: [],
                    backgroundColor: [this.colors.cyan, this.colors.purple, this.colors.emerald],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20 } }
                }
            }
        });

        // Categories (Horizontal Bar Chart)
        const ctxCategory = document.getElementById('categoryChart').getContext('2d');
        this.charts.category = new Chart(ctxCategory, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: 'rgba(124, 58, 237, 0.6)',
                    borderColor: this.colors.purple,
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { beginAtZero: true, grid: { display: false } },
                    y: { grid: { display: false } }
                }
            }
        });

        // Fix Success Rate (Bar Chart)
        const ctxSuccess = document.getElementById('fixSuccessChart').getContext('2d');
        this.charts.fixSuccess = new Chart(ctxSuccess, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.6)', // Accepted
                        'rgba(239, 68, 68, 0.6)',  // Rejected
                        'rgba(251, 191, 36, 0.6)'  // Pending
                    ],
                    borderColor: [this.colors.emerald, this.colors.red, this.colors.yellow],
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { display: false } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    async fetchStats() {
        try {
            // Simulate API call delay
            // const response = await fetch('/api/v1/stats');
            // const data = await response.json();
            
            // Using demo data for now
            const data = this.demoData;
            
            this.updateDashboard(data);
            this.updateTime();
            
        } catch (error) {
            console.error('Failed to fetch stats:', error);
            this.showToast('Failed to connect to API. Using cached data.');
            this.updateDashboard(this.demoData); // Fallback to demo
        }
    }

    updateDashboard(data) {
        // Update KPIs with animation
        this.animateNumber('kpi-total', data.kpis.totalFailures);
        this.animateNumber('kpi-resolved', data.kpis.aiResolved);
        document.getElementById('kpi-resolved-percent').textContent = `(${data.kpis.resolvedPercent}%)`;
        this.animateNumber('kpi-time', data.kpis.avgResolutionTime, 'm');
        this.animateNumber('kpi-memory', data.kpis.memoryHits);

        // Update Charts
        this.charts.failuresOverTime.data.labels = data.failuresOverTime.labels;
        this.charts.failuresOverTime.data.datasets[0].data = data.failuresOverTime.data;
        this.charts.failuresOverTime.update();

        this.charts.platform.data.datasets[0].data = data.platformStats;
        this.charts.platform.update();

        this.charts.category.data.labels = data.categories.labels;
        this.charts.category.data.datasets[0].data = data.categories.data;
        this.charts.category.update();

        this.charts.fixSuccess.data.labels = data.fixSuccess.labels;
        this.charts.fixSuccess.data.datasets[0].data = data.fixSuccess.data;
        this.charts.fixSuccess.update();

        // Update Table
        this.updateTable(data.recentFailures);
    }

    animateNumber(id, target, suffix = '') {
        const el = document.getElementById(id);
        const start = parseInt(el.textContent) || 0;
        const duration = 1500;
        const steps = 60;
        const stepTime = duration / steps;
        
        let current = start;
        const increment = (target - start) / steps;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
                el.textContent = (target % 1 !== 0 ? target.toFixed(1) : target) + suffix;
                clearInterval(timer);
            } else {
                el.textContent = (current % 1 !== 0 ? current.toFixed(1) : Math.round(current)) + suffix;
            }
        }, stepTime);
    }

    updateTable(failures) {
        const tbody = document.getElementById('recent-failures-body');
        tbody.innerHTML = '';

        failures.forEach(f => {
            const tr = document.createElement('tr');
            
            let badgeClass = '';
            if (f.status === 'resolved') badgeClass = 'resolved';
            else if (f.status === 'pending') badgeClass = 'pending';
            else badgeClass = 'failed';

            tr.innerHTML = `
                <td>${this.formatTimeAgo(f.time)}</td>
                <td>${f.platform}</td>
                <td><strong>${f.job}</strong></td>
                <td>${f.category}</td>
                <td style="max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${f.summary}</td>
                <td>${f.confidence}%</td>
                <td><span class="badge ${badgeClass}">${f.status.toUpperCase()}</span></td>
            `;
            tbody.appendChild(tr);
        });
    }

    formatTimeAgo(timestamp) {
        const seconds = Math.floor((Date.now() - timestamp) / 1000);
        
        if (seconds < 60) return `${seconds}s ago`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        return `${Math.floor(seconds / 86400)}d ago`;
    }

    updateTime() {
        const now = new Date();
        document.getElementById('refresh-time').textContent = now.toLocaleTimeString();
    }

    async sendFeedback(id, helpful) {
        try {
            // Simulate API call
            // await fetch('/api/v1/feedback', { method: 'POST', body: JSON.stringify({ id, helpful }) });
            
            this.showToast(helpful ? 'Thanks! Feedback saved.' : 'Feedback recorded. AI will learn from this.');
        } catch (error) {
            this.showToast('Failed to submit feedback.');
        }
    }

    showToast(message) {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
}

// Initialize when DOM is ready
let dashboardApp;
document.addEventListener('DOMContentLoaded', () => {
    dashboardApp = new DashboardApp();
    dashboardApp.init();
});
