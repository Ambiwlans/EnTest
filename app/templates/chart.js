{% block chart %}
<script>
const verticalLinePlugin = {
    renderVerticalLine: function (chartInstance, xVal, text) {
        const yscale = chartInstance.scales['y-axis-0'];
        const xscale = chartInstance.scales['x-axis-0'];
        const context = chartInstance.chart.ctx;
        const lineLeftOffset = xscale.getPixelForValue(xVal);
        var linecolour = '#267f00';
        if (xVal > parseInt({{scaler}} * {{pred[0]}})){linecolour = '#B40020'}
        
        // Draw another line if last one was over 20px away and not within 20px of the edge
        if (lineLeftOffset > lastVertXPx + 25 && lineLeftOffset < xscale.right - 20){
            // render vertical line
            context.beginPath();
            
            context.strokeStyle = linecolour;
            context.moveTo(lineLeftOffset, yscale.top);
            context.lineTo(lineLeftOffset, yscale.bottom);
            context.stroke();
            
            lastVertXPx = lineLeftOffset;
            
            // write label
            context.fillStyle = linecolour;
            context.textAlign = 'center';
            context.fillText(text, lineLeftOffset, (yscale.bottom - yscale.top) / 2 + yscale.top);        
        }
    },
    
    afterDatasetsDraw: function (chart, easing) {
        if (chart.config.lineAtxVal) {
            chart.config.lineAtxVal.forEach(item => this.renderVerticalLine(chart, item[0], item[1]));
        }
    }
};

function update_vert_lines(achievement_type){
    // select the set of vert lines
    switch(achievement_type){
    case 'cefr':    // default
        vert_lines = [[500,"　 　A1"],[1000,"　 　A2"],[2000,"　 　B1"],[4000,"　 　B2"],[8000,"　 　C1"],[16000,"　 　C2"]];
        break;
    case 'grade':    
        vert_lines = [[3000,"　 　Pre"],[4500," 　1"],[6000," 　2"],[7000," 　3"],[8000," 　4"],[9000," 　5"],[10000," 　6"],[10700," 　7"],[11500," 　8"],[12200," 　9"],[12900,"  　10"],[13500,"  　11"],[14000,"  　12"]];
        break;
    case 'none':    
    default:
        vert_lines = []
        break;        
    }
    lastVertXPx = 0;
    mainChart.destroy();
    mainctx = document.getElementById('predChart').getContext('2d');
    mainChart = makeChart();
};

function makePrediction() {
    var pred = []; 
    for (var x = 0; x <= parseInt({{scaler}} * {{config['MAX_X']}}) + 50; x = x + 50) {
        y = 1 / (1 + 2**({{t / scaler}} * (x - {{(a * scaler)|int}})))
        pred.push({x: x, y: y});
    }
    return pred;
};

function rightPoints(val) {
    return {x: parseInt({{scaler}} * val[0]), y: 1, question: val[1]};
};

function wrongPoints(val) {
    return {x: parseInt({{scaler}} * val[0]), y: 0, question: val[1]};
};

var lastVertXPx = 0;
var vert_lines = [[500,"　 　A1"],[1000,"　 　A2"],[2000,"　 　GB1"],[4000,"　 　B2"],[8000,"　 　C1"],[16000,"　 　C2"]];
var prediction =  makePrediction();
var mainctx = document.getElementById('predChart').getContext('2d');
var mainChart = makeChart();

function makeChart(){
return new Chart(mainctx, {
    type: 'line',
    data: {
        datasets: [{
            type: 'scatter',
            showLine: false,
            data: {{ rightanswers|tojson|safe }}.map(rightPoints),
            pointBackgroundColor: '#267f00'
        }, {
            type: 'scatter',
            showLine: false,
            data: {{ wronganswers|tojson|safe }}.map(wrongPoints),
            pointBackgroundColor: '#B40020'
        }, {
            type: 'line',
            label: 'Prediction',
            backgroundColor: '#267f0020',
            fill: 'origin',
            data: prediction,
            pointRadius: 0
        }, {
            type: 'line',
            label: 'Prediction',
            backgroundColor: '#B4002020',
            fill: 'end',
            data: prediction,
            pointRadius: 0
        }]
    },
    plugins: [verticalLinePlugin],
    lineAtxVal: vert_lines,
    options: {
        responsive: true,
        maintainAspectRatio: false,
        tooltips: {
            enabled: true,
            mode: 'single',
            bodyFontSize: 18,
            callbacks: {
                custom: function(tooltip) {
    		        if (!tooltip) return;
    		        // disable displaying the color box;
    		        tooltip.displayColors = false;
		        },
                label: function(tooltipItems, data) { 
                    return (data.datasets[tooltipItems.datasetIndex].data[tooltipItems.index].question);
                },
                title: function(tooltipItem, data) {
		          return;
		        }
            }
        },
        scales: {
            xAxes: [{
                type: 'linear',
                beginAtZero: true,
                ticks: {
                    max: {{((scaler * xmax / 500)|round(0, 'ceil')) * 500}}
                }
            }],
            yAxes: [{
                ticks: {
                    beginAtZero: true,
                    callback: function(value, index, values) {
                        if (value == 0 || value == .5 || value == 1){
                            return (value * 100) + '%';
                        }
                        return '';
                    }
                }
            }]
        },
        legend: {
            display: false
        },
        layout: {
            padding: {
                top: 30
            }
        },
        animation: {
            duration: 0
        }
    }
});};


</script>
{% endblock chart %}