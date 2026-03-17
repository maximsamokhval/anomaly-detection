/**
 * Chart.js initialization utilities for Financial Anomaly Detection Service.
 * 
 * This file provides common chart configurations used across templates.
 * In Static UI (Phase 1), charts use mock data. In Phase 2+, data is fetched from API.
 */

/**
 * Default chart options for time series charts.
 */
export const defaultChartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
        legend: {
            display: true,
            position: 'top'
        },
        tooltip: {
            callbacks: {
                label: function(context) {
                    return context.dataset.label + ': ' + context.parsed.y.toFixed(2);
                }
            }
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            title: {
                display: true,
                text: 'Value'
            }
        },
        x: {
            title: {
                display: true,
                text: 'Period'
            }
        }
    }
};

/**
 * Create a time series line chart.
 * @param {string} canvasId - The ID of the canvas element
 * @param {Array} labels - Array of period labels (dates)
 * @param {Array} data - Array of values
 * @param {string} label - Dataset label
 * @param {Array} anomalyIndices - Indices where anomalies occur
 */
export function createTimeSeriesChart(canvasId, labels, data, label = 'Value', anomalyIndices = []) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const backgroundColor = anomalyIndices.map((_, i) => {
        return anomalyIndices.includes(i) 
            ? 'rgba(245, 158, 11, 0.2)'  // Orange for anomalies
            : 'rgba(75, 192, 192, 0.2)';  // Teal for normal
    });
    
    const borderColor = anomalyIndices.map((_, i) => {
        return anomalyIndices.includes(i)
            ? 'rgb(245, 158, 11)'  // Orange for anomalies
            : 'rgb(75, 192, 192)';  // Teal for normal
    });
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: borderColor,
                backgroundColor: backgroundColor,
                tension: 0.1,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: borderColor,
            }]
        },
        options: defaultChartOptions
    });
}

/**
 * Color palette for anomaly types.
 */
export const anomalyColors = {
    ZERO_NEG: { bg: 'rgba(220, 38, 38, 0.2)', border: 'rgb(220, 38, 38)' },
    SPIKE: { bg: 'rgba(245, 158, 11, 0.2)', border: 'rgb(245, 158, 11)' },
    RATIO: { bg: 'rgba(139, 92, 246, 0.2)', border: 'rgb(139, 92, 246)' },
    TREND_BREAK: { bg: 'rgba(59, 130, 246, 0.2)', border: 'rgb(59, 130, 246)' },
    MISSING: { bg: 'rgba(107, 114, 128, 0.2)', border: 'rgb(107, 114, 128)' },
    MISSING_DATA: { bg: 'rgba(156, 163, 175, 0.2)', border: 'rgb(156, 163, 175)' },
};

/**
 * Get color for anomaly type.
 * @param {string} anomalyType - The anomaly type
 * @returns {Object} Color object with bg and border
 */
export function getAnomalyColor(anomalyType) {
    return anomalyColors[anomalyType] || anomalyColors.MISSING;
}

// Export for use in templates
if (typeof window !== 'undefined') {
    window.AnomalyCharts = {
        createTimeSeriesChart,
        defaultChartOptions,
        anomalyColors,
        getAnomalyColor
    };
}
