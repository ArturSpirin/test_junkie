

class ReportTemplate:

    LABEL_COLOR = "#aebac4"

    @staticmethod
    def get_body_template():

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
                        <style>
                            .absolute_cards{{
                                min-height: 170px;
                                overflow: hidden;
                            }}
                            
                            .absolute_value{{
                                font-size: 27px;
                            }}
                            
                            .card:hover {{
                                background: #193746 !important;
                                transition: all .3s ease-in;
                            }}
                        </style>
                        {body}
                    </body>
                </html> 
               """

    @staticmethod
    def get_tiny_card_template(label, data):

        return """
                <div class="col s6 m4 l3 xl2">
                  <div class="card blue-grey darken-3 absolute_cards">
                    <div class="card-content white-text">
                      <span class="card-title">{label}</span>
                      <div class="absolute_value"><b>{data}</b></div>
                    </div>
                  </div>
                </div>
               """.format(label=label, data=data)

    @staticmethod
    def get_resource_chart_template(resource, data, labels):

        def js():

            return """
                    <script>
                    var {resource} = document.getElementById('{resource}Chart').getContext('2d');
                    var {resource}_labels = {labels}
                    var labels = []
                    for(var label in {resource}_labels){
                        labels.push(new Date({resource}_labels[label]))
                    }
                    var data = {
                        labels: labels,
                        datasets: [{data}]
                    }
                    const {resource}_options = {
                        type: 'line',
                        data: data,
                        options: {
                            legend: {labels: {fontColor: '{label_color}'}},
                            fill: false,
                            responsive: true,
                            scales: {
                                xAxes: [{
                                    ticks: {fontColor: '{label_color}'},
                                    type: 'time',
                                    time: {unit: 'second'},
                                    display: true,
                                    scaleLabel: {
                                        display: true,
                                        labelString: 'time',
                                    }
                                }],
                                yAxes: [{
                                    ticks: {
                                        fontColor: '{label_color}',
                                        beginAtZero: true,
                                    },
                                    display: true,
                                    scaleLabel: {
                                        display: true,
                                        labelString: 'usage %',
                                    }
                                }]
                            }
                        }
                    }
                    const {resource}_chart = new Chart({resource}, {resource}_options);
                    </script>
                   """.replace("{resource}", resource)\
                      .replace("{data}", data)\
                      .replace("{labels}", labels)\
                      .replace("{label_color}", ReportTemplate.LABEL_COLOR)

        return """
                <div class='col s12 m12 l6 xl4'>
                  <div class='card blue-grey darken-3'>
                    <div class='card-content white-text'>
                      <span class='card-title'>{resource}:</span>
                      <span>Resource monitoring disabled</span>
                      <canvas id='{resource}Chart'></canvas>
                    </div>
                  </div>
                </div>
                {js}
               """.format(js=js(), resource=resource, data=data, labels=labels)

    @staticmethod
    def get_absolute_results_template(data):

        def js():

            return """
                    <script>
                    var totals = document.getElementById('totals').getContext('2d');
                    var myPieChart = new Chart(totals,{
                        type: 'pie',
                        data: {data},
                        options: {legend: {labels: {fontColor: '{label_color}'}}}
                    });
                    </script>
                   """.replace("{data}", data)\
                      .replace("{label_color}", ReportTemplate.LABEL_COLOR)

        return """
                <div class="col s12 m12 l6 xl4">
                  <div class="card blue-grey darken-3">
                    <div class="card-content white-text">
                      <span class="card-title">Absolute Results:</span>
                      <canvas id="totals"></canvas>
                    </div>
                  </div>
                </div>
                {js}
               """.format(js=js())

    @staticmethod
    def get_stacked_bar_results_template(resource_id, data, label):

        def js():

            return """
                    <script>
                    var by_{resource} = document.getElementById('by_{resource}').getContext('2d');
                    var by_{resource}_chart = new Chart(by_{resource}, {
                        type: 'bar',
                        data: {data},
                        options: {
                            legend: {labels: {fontColor: '{label_color}'}},
                            scales: {
                                xAxes: [{
                                    ticks: {fontColor: "{label_color}"},
                                    stacked: true
                                }],
                                yAxes: [{
                                    ticks: {fontColor: "{label_color}"},
                                    stacked: true
                                }]
                            }
                        }
                    });
                    </script>
                   """.replace("{resource}", resource_id)\
                      .replace("{data}", data)\
                      .replace("{label_color}", ReportTemplate.LABEL_COLOR)

        return """
                <div class="col s12 m12 l6 xl4">
                  <div class="card blue-grey darken-3">
                    <div class="card-content white-text">
                      <span class="card-title">Results by {label}:</span>
                      <canvas id="by_{resource}"></canvas>
                    </div>
                  </div>
                </div>
                {js}
               """.format(js=js(), resource=resource_id, label=label)
