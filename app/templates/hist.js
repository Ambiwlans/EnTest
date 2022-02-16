{% block chart %}
<script>

var ctx = document.getElementById('histChart').getContext('2d');
var myLineChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: {{ hist|tojson|safe }}.map(histlabels),
        datasets: [{
            data: {{ hist|tojson|safe }}.map(histdata),
            backgroundColor: {{ hist|tojson|safe }}.map(histcolours)
        }]
        
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                grid: {
                    offset: true
                }
            },
        },
        legend: {
            display: false
        },
        animation: {
            duration: 0
        }
    }
});

function histdata(val) {
    return val[1];
};

function histlabels(val) {
    //console.log(JSON.stringify((parseInt({{scaler}} * val[0])));
    return parseInt({{scaler}} * val[0]);
};

function histcolours(val, i, ele) {
    if (ele[i][0] > {{avg}}){return "grey";}
    if (ele[i+1][0] < {{avg}}){return "grey"}
    return "green"
};

</script>
{% endblock chart %}