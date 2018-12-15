

class ReportTemplate:

    @staticmethod
    def get_html_template():

        return """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Report</title>
        <script src="https://code.jquery.com/jquery-3.3.1.min.js"
                integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8="
                crossorigin="anonymous"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.7.3/Chart.bundle.min.js"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js"></script>
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    </head>
<body style="background-color: #3d4f58;">

<div class="row">
    <div class="col s6 m4 l3 xl2">
      <div class="card blue-grey darken-3 absolute_cards">
        <div class="card-content white-text">
          <span class="card-title">Total Tests Executed:</span>
          <div class="absolute_value"><b>{total_test_executed}</b></div>
        </div>
      </div>
    </div>
    <div class="col s6 m4 l3 xl2">
      <div class="card blue-grey darken-3 absolute_cards">
        <div class="card-content white-text">
          <span class="card-title">Passing Rate:</span>
          <div class="absolute_value"><b>{absolute_passing_rate}%</b></div>
        </div>
      </div>
    </div>
    <div class="col s6 m4 l3 xl2">
      <div class="card blue-grey darken-3 absolute_cards">
        <div class="card-content white-text">
          <span class="card-title">Average Test Runtime:</span>
          <div class="absolute_value"><b>{average_test_runtime}</b></div>
        </div>
      </div>
    </div>
    <div class="col s6 m4 l3 xl2">
      <div class="card blue-grey darken-3 absolute_cards">
        <div class="card-content white-text">
          <span class="card-title">Total Runtime:</span>
          <div class="absolute_value"><b>{total_runtime}</b></div>
        </div>
      </div>
    </div>
    <div class="col s6 m4 l3 xl2">
      <div class="card blue-grey darken-3 absolute_cards">
        <div class="card-content white-text">
          <span class="card-title">Average CPU</span>
          <div class="absolute_value"><b>{average_cpu}%</b></div>
        </div>
      </div>
    </div>
    <div class="col s6 m4 l3 xl2">
      <div class="card blue-grey darken-3 absolute_cards">
        <div class="card-content white-text">
          <span class="card-title">Average MEM</span>
          <div class="absolute_value"><b>{average_mem}%</b></div>
        </div>
      </div>
    </div>
</div>

<div class="row">

    <div class="col s12 m12 l6 xl4">
      <div class="card blue-grey darken-3">
        <div class="card-content white-text">
          <span class="card-title">CPU Trend:</span>
          <span>Resource monitoring disabled</span>
          <canvas id="CPUChart"></canvas>
        </div>
      </div>
    </div>

    <div class="col s12 m12 l6 xl4">
      <div class="card blue-grey darken-3">
        <div class="card-content white-text">
          <span class="card-title">MEM Trend:</span>
          <span>Resource monitoring disabled</span>
          <canvas id="MEMChart"></canvas>
        </div>
      </div>
    </div>

    <div class="col s12 m12 l6 xl4">
      <div class="card blue-grey darken-3">
        <div class="card-content white-text">
          <span class="card-title">Absolute Results:</span>
          <canvas id="totals"></canvas>
        </div>
      </div>
    </div>

<script>

var cpu = document.getElementById('CPUChart').getContext('2d');
var cpu_labels = {cpu_labels}
var labels = []
for(var label in cpu_labels){
    labels.push(new Date(""+cpu_labels[label]+""))
}
var data = {
    labels: labels,
    datasets: [{cpu_data}]
}
const cpu_options = {
    type: 'line',
    data: data,
    options: {
        legend: {
            labels: {
                fontColor: '#e5e5e5'
            }
        },
        fill: false,
        responsive: true,
        scales: {
            xAxes: [{
                type: 'time',
                time: {
                    unit: 'second'
                },
                display: true,
                scaleLabel: {
                    display: true,
                    labelString: "time",
                }
            }],
            yAxes: [{
                ticks: {
                    beginAtZero: true,
                },
                display: true,
                scaleLabel: {
                    display: true,
                    labelString: "usage %",
                }
            }]
        }
    }
}
const cpu_chart = new Chart(cpu, cpu_options);

</script>

<script>

var mem = document.getElementById('MEMChart').getContext('2d');
var mem_labels = {mem_labels}
var labels = []
for(var label in mem_labels){
    labels.push(new Date(""+mem_labels[label]+""))
}
var data = {
    // Labels should be Date objects new Date(unix_timestamp  * 1000)
    labels: labels,
    datasets: [{mem_data}]
}
const mem_options = {
    type: 'line',
    data: data,
    options: {
        legend: {
            labels: {
                fontColor: '#e5e5e5'
            }
        },
        fill: false,
        responsive: true,
        scales: {
            xAxes: [{
                type: 'time',
                time: {
                    unit: 'second'
                },
                display: true,
                scaleLabel: {
                    display: true,
                    labelString: "time",
                }
            }],
            yAxes: [{
                ticks: {
                    beginAtZero: true,
                },
                display: true,
                scaleLabel: {
                    display: true,
                    labelString: "usage %",
                }
            }]
        }
    }
}
const mem_chart = new Chart(mem, mem_options);

</script>


<script>

var totals = document.getElementById('totals').getContext('2d');
var myPieChart = new Chart(totals,{
    type: 'pie',
    data: {absolute_data},
    options: {
        legend: {
            labels: {
                fontColor: '#e5e5e5'
            }
        }
    }
});

</script>

</div>

<div class="row">
    <div class="col s12 m12 l6 xl4">
      <div class="card blue-grey darken-3">
        <div class="card-content white-text">
          <span class="card-title">Results by Features:</span>
          <canvas id="by_features"></canvas>
        </div>
      </div>
    </div>
    <div class="col s12 m12 l6 xl4">
      <div class="card blue-grey darken-3">
        <div class="card-content white-text">
          <span class="card-title">Results by Tags:</span>
          <canvas id="by_tags"></canvas>
        </div>
      </div>
    </div>
    <div class="col s12 m12 l6 xl4">
      <div class="card blue-grey darken-3">
        <div class="card-content white-text">
          <span class="card-title">Results by Owner:</span>
          <canvas id="by_owners"></canvas>
        </div>
      </div>
    </div>
</div>

<script>

var by_features = document.getElementById('by_features').getContext('2d');
var by_features_chart = new Chart(by_features, {
    type: 'bar',
    data: {features_data},
    options: {
        legend: {
            labels: {
                fontColor: '#e5e5e5'
            }
        },
        scales: {
            xAxes: [{
                stacked: true
            }],
            yAxes: [{
                stacked: true
            }]
        }
    }
});

</script>

<script>

var by_tags = document.getElementById('by_tags').getContext('2d');
var by_tags_chart = new Chart(by_tags, {
    type: 'bar',
    data: {tags_data},
    options: {
        legend: {
            labels: {
                fontColor: '#e5e5e5'
            }
        },
        scales: {
            xAxes: [{
                stacked: true
            }],
            yAxes: [{
                stacked: true
            }]
        }
    }
});

</script>

<script>

var by_owners = document.getElementById('by_owners').getContext('2d');
var by_owners_chart = new Chart(by_owners, {
    type: 'bar',
    data: {owners_data},
    options: {
        legend: {
            labels: {
                fontColor: '#e5e5e5'
            }
        },
        scales: {
            xAxes: [{
                stacked: true
            }],
            yAxes: [{
                stacked: true
            }]
        }
    }
});

</script>

<style>
.absolute_cards{
    min-height: 170px;
    overflow: hidden;
}

.absolute_value{
    font-size: 27px;
}

.card:hover {
    background: #193746 !important;
    transition: all .3s ease-in;
}
</style>

<div class="fixed-action-btn horizontal">
  <a class="btn-floating btn-large deep-orange">
    <i class="large material-icons">monetization_on</i>
  </a>
  <ul>
    <li>
        <a href="https://www.patreon.com/join/arturspirin/"
           id="become_patreon" class="btn-floating green tooltipped" data-position="top"
           data-tooltip="Support Test Junkie by backing it's creator on Patreon">
            <i class="material-icons">people</i>
        </a>
    </li>
    <li aria-disabled="true">
        <a href="https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=FJPYWX5B776YS&currency_code=USD&source=url"
           id="donate" class="btn-floating light-blue darken-1 tooltipped" data-position="top"
           data-tooltip="Support Test Junkie by donating to it's creator through PayPal">
            <i class="material-icons">payment</i>
        </a>
    </li>
  </ul>
</div>

</body>
</html> 
"""
