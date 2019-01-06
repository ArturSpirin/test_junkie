from test_junkie.constants import TestCategory


class ReportTemplate:

    LABEL_COLOR = "#aebac4"

    @staticmethod
    def get_body_template():
        return """
                <!DOCTYPE html>
                <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <title>Test Junkie HTML Report</title>
                        <script src="https://code.jquery.com/jquery-3.3.1.min.js"
                                integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8="
                                crossorigin="anonymous"></script>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.7.3/Chart.bundle.min.js"></script>
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css">
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js"></script>
                        <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
                        <link href="https://cdn.datatables.net/1.10.19/css/jquery.dataTables.min.css" rel="stylesheet">
                        <script src="https://www.amcharts.com/lib/4/core.js"></script>
                        <script src="https://www.amcharts.com/lib/4/charts.js"></script>
                        <script src="https://www.amcharts.com/lib/4/themes/dark.js"></script>
                        <script src="https://www.amcharts.com/lib/4/themes/animated.js"></script>
                        <script src="https://cdn.datatables.net/1.10.19/js/jquery.dataTables.min.js"></script>
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
                            
                            body {{
                                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
                            }}
                        </style>
                        {body}
                    </body>
                </html> 
               """

    @staticmethod
    def get_donation_options():

        return """
                <div class="fixed-action-btn horizontal">
                    <a class="btn-floating btn-large waves-effect waves-light orange darken-4 modal-trigger" href="#developerModal"><i class="material-icons">favorite</i></a>
                </div>
                <script>
                    $(document).ready(function(){
                        $('.modal').modal();
                    });
                </script>
                <div id="developerModal" class="modal">
                    <div class="modal-content" style="color: black;">
                      <h4>Greetings!</h4>
                        <p>Some features are not yet finished. 
                           I'm <a href="https://www.linkedin.com/in/arturspirin/" target="_blank">Artur</a>
                           by the way, the developer of
                           <a href="https://github.com/ArturSpirin/test_junkie" target="_blank">Test Junkie</a></p>
                        <br>
                        <p>It took a lot of effort, all my free time outside my day job, and many sleepless
                            nights to get this project to this point, that includes styling and doing data
                            processing in order to render all those charts and tables. I have been motivated by
                            the idea that it may become useful for testers, QA managers, QA team leads, and
                            even project managers and developers. Thus I open sourced this project initially
                            knowing that I wont make much (if any at all) money by doing it.</p>
                        <br>
                        <p>Ask yourself if all the effort I put in and the benefits Test Junkie brings to you
                            and/or your company (if any) are worth a donation. This donation will keep me
                            motivated and directly support this project.</p>
                        <br>
                        <p>Ways you can donate:</p>
                        <ol>
                            <li>Share Test Junkie on social media, with your friend and/or colleagues.
                                Tell them how it helped you in your project.</li>
                            <li>Write me a message on <a href="https://www.linkedin.com/in/arturspirin/"
                                                         target="_blank">Linked In</a> and tell me about your
                                experience with Test Junkie.</li>
                            <li>If you can afford, you can donate through
                                <a href="https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=FJPYWX5B776YS
                                &currency_code=USD&source=url" target="_blank">PayPal</a>.
                                No amount is small amount, its the thought that counts!</li>
                            <li>You can also back me on
                                <a href="https://www.patreon.com/join/arturspirin/" target="_blank">Patreon</a>
                                on behalf of your company and get some benefits by doing so.</li>
                        </ol>
                        <p>Happy testing!</p>


                    </div>
                    <div class="modal-footer">
                      <a href="#!" class="modal-close waves-effect waves-green btn-flat">Close</a>
                    </div>
                </div>
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
    def get_table(data):
        def css():
            return """
                   <style>
                        table.dataTable thead th, table.dataTable thead td, table.dataTable.no-footer{
                        border: 0px !important;}
                        table.dataTable.no-footer{padding-bottom: 10px;}
                        #table_results tr{background: transparent;}
                        #table_results tbody tr:hover{
                            background: #1e4254;
                            cursor: pointer;
                            border-radius: 3px;}
                        #table_results_info{color: #ffffff;}
                        .dataTables_wrapper .dataTables_paginate{padding-right:50px;}
                        .dataTables_wrapper .dataTables_paginate .paginate_button.current, .dataTables_wrapper .dataTables_paginate .paginate_button {
                            color: #ffffff !important;
                            background: transparent !important;
                            border: 1px transparent!important;}
                        .dataTables_wrapper .dataTables_paginate .paginate_button.current, .dataTables_wrapper .dataTables_paginate .paginate_button.current:hover {
                            color: #ffffff !important;
                            border-bottom: 2px #fff !important;}
                        .dataTables_wrapper .dataTables_paginate .paginate_button:hover {
                            background: transparent !important;
                            border: 1px transparent!important;}
                        .dataTables_wrapper .dataTables_paginate .paginate_button:active {
                            background: transparent !important;
                            border: 1px transparent!important;}
                        .dataTables_wrapper .dataTables_paginate .paginate_button.current{
                            background: #1e4254 !important;}
                   </style>
                   """

        def js():
            return """
                   <script>
                        $(document).ready(function() {

                            var table = $("#table_results").DataTable( {
                                deferRender: true,
                                data: {data},
                                displayLength: 25,
                                order: [[ 0, "asc" ]],
                                columns: [
                                    {
                                        title: "Suite Name" ,
                                        mDataProp: "suite",
                                        defaultContent: "N/A"},
                                    {
                                        title: "Test Name" ,
                                        mDataProp: "test",
                                        defaultContent: "N/A"},
                                    {
                                        title: "Feature" ,
                                        mDataProp: "feature",
                                        defaultContent: "N/A"},
                                    {
                                        title: "Component" ,
                                        mDataProp: "component",
                                        defaultContent: "N/A"},
                                    {
                                        title: "Duration" ,
                                        mDataProp: "duration",
                                        defaultContent: "N/A"},
                                    {
                                        title: "Status" ,
                                        mDataProp: "status",
                                        defaultContent: "N/A"}],
                                createdRow: function(row, data, index){
                                    row.setAttribute("href", "#developerModal")
                                    row.setAttribute('class', 'modal-trigger')
                                }
                            });

                            var example_length = $('#table_results_length');
                            var example_filter = $('#table_results_filter');
                            example_filter.html("")
                            example_length.html("")

                             $('#table_results thead th').each(function(){
                                var title = $('#table_results thead th').eq($(this).index()).text();
                                $(this).html('<input class="deletable" id="search'+$('#table_results thead th').eq($(this).index()).text()+'" type="text" placeholder="'+title+'"/>');
                            });

                            table.columns().every(function(){
                                var tableColumn = this;
                                var input = $(this.header()).find('input');

                                input.on('change', function(){
                                    tableColumn.search(this.value).draw();
                                });
                                input.on('click', function(e){
                                    e.stopPropagation();
                                });
                                input.keyup(function(e){
                                    tableColumn.search(this.value).draw();
                                    input.focus();
                                });
                                input.keydown(function(e){
                                    if (e.keyCode == 65 && e.ctrlKey) {
                                        e.target.select()
                                    }
                                });
                            });
                        });
                   </script>
                   """.replace("{data}", str(data))

        return """
                <div class="row">
                    <div class="col s12 m12 l12 xl12">
                      <div class="card blue-grey darken-3">
                            <div class="card-content white-text">
                                <table id="table_results" class="mdl-data-table" >
                                {css}
                                {js}
                            </div>
                        </div>
                    </div>
                </div>
               """.format(css=css(), js=js())

    @staticmethod
    def get_resource_chart_template(data):
        """
        :param data: LIST of DICTs aka
                     [{date: newDate, cpu: cpu, mem: mem},
                      {date: newDate, cpu: cpu, mem: mem}]
        :return: STRING, HTML for the CPU & MEM chart
        """
        doc_link = "<span>Resource monitoring disabled. See <a href=\"{link}\">documentation</a> to enabled it.</span>"

        def css():

            return """
                   <style>
                        #resources {
                            width: 100%;
                            height: 282px;
                        }
                   </style>
                   """

        def js():

            return """
                   <script>
                   $(document).ready(function() {
                        // Themes
                        am4core.useTheme(am4themes_dark);
                        am4core.useTheme(am4themes_animated);
                        
                        // Create chart
                        var chart = am4core.create("resources", am4charts.XYChart);
                        chart.paddingRight = 20;
                        
                        // format data
                        var data = {data};
                        for(dict in data){
                            console.log(data[dict].date)
                            data[dict].date = new Date(data[dict].date)
                            console.log(data[dict].date)
                        }
                        
                        chart.data = data;
    
                        var dateAxis = chart.xAxes.push(new am4charts.DateAxis());
                        dateAxis.baseInterval = {
                          "timeUnit": "second",
                          "count": 1
                        };
                        dateAxis.tooltipDateFormat = "HH:mm:ss, d MMMM";
    
                        var valueAxis = chart.yAxes.push(new am4charts.ValueAxis());
                        valueAxis.tooltip.disabled = true;
                        valueAxis.title.text = "Usage %";
                        valueAxis.strictMinMax  = 100;
    
                        function createSeries(field, name){
                          var series = chart.series.push(new am4charts.LineSeries());
                          series.name = name;
                          series.dataFields.dateX = "date";
                          series.dataFields.valueY = field;
                          series.tooltipText = name+": [bold]{valueY}%[/]";
                          series.fillOpacity = 0.3;
                          return series
                        }
    
                        createSeries("cpu", "cpu")
                        createSeries("mem", "mem")
                        chart.cursor = new am4charts.XYCursor();
                        chart.cursor.lineY.opacity = 0;
                    });
                   </script>
                   """.replace("{data}", str(data))

        return """
                <div class='col s12 m12 l6 xl6'>
                  <div class='card blue-grey darken-3'>
                    <div class='card-content white-text'>
                      <span class='card-title'>CPU & Memory Usage:</span>
                      {doc_link}
                      <div id="resources"></div>
                      {css}
                      {js}
                    </div>
                  </div>
                </div>
               """.format(css=css(), js=js(), doc_link=doc_link if not data else "")

    @staticmethod
    def get_absolute_results_template(data, colors):
        """
        Colors need to come with the data as well
        :param data: LIST of DICTs aka
                     [{status: "Pass", value: 401},
                      {status: "Fail", value: 300},
                      {status: "Error", value: 200},
                      {status: "Ignore", value: 165},
                      {status: "Canceled", value: 139},
                      {status: "Skipped", value: 128}]
        :return: STRING, HTML for the Absolute Metrics chart
        """
        def css():

            return """
                   <style>
                       #absolute_metrics{
                            width: 100%;
                            height: 282px;
                       }
                   </style>
                   """

        def js():

            return """
                   <script>
                        // Theme
                        am4core.useTheme(am4themes_dark);
                        am4core.useTheme(am4themes_animated);

                        var chart = am4core.create("absolute_metrics", am4charts.PieChart);
                        chart.hiddenState.properties.opacity = 0; // this creates initial fade-in

                        chart.data = {data};
                        chart.radius = am4core.percent(70);
                        chart.innerRadius = am4core.percent(40);
                        chart.startAngle = 180;
                        chart.endAngle = 360;

                        var series = chart.series.push(new am4charts.PieSeries());
                        
                        // format colors
                        var colors = {colors}
                        for (item in colors) colors[item] = am4core.color(colors[item]) 
                        series.colors.list = colors;
                        
                        series.dataFields.value = "value";
                        series.dataFields.category = "status";
                        series.slices.template.cornerRadius = 10;
                        series.slices.template.innerCornerRadius = 7;
                        series.slices.template.draggable = true;
                        series.slices.template.inert = true;
                        series.alignLabels = false;
                        series.hiddenState.properties.startAngle = 90;
                        series.hiddenState.properties.endAngle = 90;
                   </script>
                   """.replace("{data}", str(data)).replace("{colors}", str(colors))

        return """
                <div class="col s12 m12 l6 xl6">
                  <div class="card blue-grey darken-3">
                    <div class="card-content white-text">
                      <span class="card-title">Absolute Metrics:</span>
                        <div id="absolute_metrics"></div>
                        {css}
                        {js}
                    </div>
                  </div>
                </div>
               """.format(css=css(), js=js())

    @staticmethod
    def get_stacked_bar_results_template(features_data, components_data, team_data, suites_data, tags_data):
        """
        All data must be passed in in the following format:
        [{"duration": 10,
          "measure": "Login",
          "passed": 227,
          "error": 10,
          "cancel": 12,
          "ignore": 40,
          "failed": 408
        }, {"duration": 10,
            "measure": "Dashboard",
            "passed": 371,
            "error": 10,
            "cancel": 7,
            "ignore": 38,
            "failed": 482}, ...]
        :param features_data: LIST of DICTs
        :param components_data: LIST of DICTs
        :param team_data: LIST of DICTs
        :param suites_data: LIST of DICTs
        :param tags_data: LIST of DICTs
        :return: STRING, HTML for all the charts in the tabs
        """

        series = []
        from test_junkie.reporter.reporter import Reporter
        for status in TestCategory.ALL:
            series.append({"status": status, "label": status, "color": Reporter.COLOR_MAPPING[status]})

        def css(chart_id):

            return """
                    <style>
                        #{chart_id} {{
                            width: 100%;
                            height: 400px;
                        }}
                    </style>
                   """.format(chart_id=chart_id)

        def js(chart_id, chart_data):

            return """
                   <script>
                   $(document).ready(function() {
                        // Themes begin
                        am4core.useTheme(am4themes_animated);
                        am4core.useTheme(am4themes_dark);
                        // Create chart instance
                        var chart_{chart_id} = am4core.create("{chart_id}", am4charts.XYChart);
                        
                        // Add data
                        chart_{chart_id}.data = {data}
                        
                        // Create axes
                        var categoryAxis_{chart_id} = chart_{chart_id}.xAxes.push(new am4charts.CategoryAxis());
                        categoryAxis_{chart_id}.dataFields.category = "measure";
                        categoryAxis_{chart_id}.renderer.grid.template.location = 0;
                        
                        var valueAxis_{chart_id} = chart_{chart_id}.yAxes.push(new am4charts.ValueAxis());
                        valueAxis_{chart_id}.renderer.inside = true;
                        valueAxis_{chart_id}.renderer.labels.template.disabled = true;
                        valueAxis_{chart_id}.min = 0;
                        
                        var testsAxis_{chart_id} = chart_{chart_id}.yAxes.push(new am4charts.ValueAxis());
                        testsAxis_{chart_id}.title.text = "Tests";
                        testsAxis_{chart_id}.renderer.grid.template.disabled = true;
                        
                        var durationAxis_{chart_id} = chart_{chart_id}.yAxes.push(new am4charts.DurationAxis());
                        durationAxis_{chart_id}.title.text = "Average Test Duration";
                        durationAxis_{chart_id}.baseUnit = "second";
                        durationAxis_{chart_id}.renderer.grid.template.disabled = true;
                        durationAxis_{chart_id}.renderer.opposite = true;
                        durationAxis_{chart_id}.durationFormatter.durationFormat = "h'h' m'min' s'sec'";
                        
                        // Create series
                        function createSeries(field, name, color) {
                              // Set up series
                              var series_{chart_id} = chart_{chart_id}.series.push(new am4charts.ColumnSeries());
                              series_{chart_id}.name = name;
                              series_{chart_id}.yAxis = testsAxis_{chart_id};
                              series_{chart_id}.dataFields.valueY = field;
                              series_{chart_id}.dataFields.categoryX = "measure";
                              series_{chart_id}.sequencedInterpolation = true;
                            
                              // Make it stacked
                              series_{chart_id}.stacked = true;
                            
                              // Configure columns
                              series_{chart_id}.columns.template.width = am4core.percent(60);
                              series_{chart_id}.columns.template.tooltipText = "[bold]{name}[/]\\n[font-size:14px]{categoryX}: {valueY}";
                              series_{chart_id}.columns.template.stroke = am4core.color(color);
                              series_{chart_id}.columns.template.fill = am4core.color(color);
                              series_{chart_id}.columns.template.fillOpacity = 0.9;
                              return series_{chart_id};
                        }
                        
                        var required_series_{chart_id} = {series}
                        for(entry in required_series_{chart_id}){
                            createSeries(required_series_{chart_id}[entry].status, required_series_{chart_id}[entry].label, required_series_{chart_id}[entry].color)
                        }
                        
                        var durationSeries_{chart_id} = chart_{chart_id}.series.push(new am4charts.LineSeries());
                        durationSeries_{chart_id}.dataFields.valueY = "duration";
                        durationSeries_{chart_id}.dataFields.categoryX = "measure";
                        durationSeries_{chart_id}.yAxis = durationAxis_{chart_id};
                        durationSeries_{chart_id}.name = "Duration";
                        durationSeries_{chart_id}.strokeWidth = 2;
                        durationSeries_{chart_id}.stroke = am4core.color("#03a2cd");
                        durationSeries_{chart_id}.tooltip.getFillFromObject = false;
                        durationSeries_{chart_id}.tooltip.background.fill = am4core.color("#03a2cd");
                        durationSeries_{chart_id}.tooltipText = "{valueY.formatDuration()}";
                        
                        // Legend
                        chart_{chart_id}.legend = new am4charts.Legend();
                        
                        // Add cursor
                        chart_{chart_id}.cursor = new am4charts.XYCursor();
                        chart_{chart_id}.cursor.fullWidthLineX = true;
                        chart_{chart_id}.cursor.xAxis = valueAxis_{chart_id};
                        chart_{chart_id}.cursor.lineX.strokeOpacity = 0;
                        chart_{chart_id}.cursor.lineX.fill = am4core.color("#000");
                        chart_{chart_id}.cursor.lineX.fillOpacity = 0.1;
                    });
                   </script>
                   """.replace("{data}", str(chart_data))\
                      .replace("{chart_id}", chart_id)\
                      .replace("{series}", str(series))

        def card(chart_id, title, chart_data):
            return """
                   <div id="{chart_id}_tab" class="col s12">
                       <div class="col s12 m12 l12 xl12">
                         <div class="card blue-grey darken-3">
                           <div class="card-content white-text">
                             <span class="card-title">{title}:</span>
                             <div id="{chart_id}"></div>
                             {css}
                             {js}
                           </div>
                         </div>
                       </div>
                   </div>
                   """.format(chart_id=chart_id, title=title, css=css(chart_id), js=js(chart_id, chart_data))

        features_html = card("features", "Results by Features", features_data)
        components_html = card("components", "Results by Components", components_data)
        team_html = card("owners", "Results by Assignees", team_data)
        suites_html = card("suites", "Results by Test Suites", suites_data)
        tags_html = card("tags", "Results by Tags", tags_data)

        return """
                <div class="row">
                    <div class="col s12 m12 l12 xl12">
                      <ul class="tabs transparent" style="margin-left: 20px;">
                        <li class="tab col s2"><a class="blue-text text-lighten-2 active" href="#features_tab">Features</a></li>
                        <li class="tab col s2"><a class="blue-text text-lighten-2" href="#components_tab">Components</a></li>
                        <li class="tab col s2"><a class="blue-text text-lighten-2" href="#owners_tab">Team</a></li>
                        <li class="tab col s2"><a class="blue-text text-lighten-2" href="#suites_tab">Suites</a></li>
                        <li class="tab col s2"><a class="blue-text text-lighten-2" href="#tags_tab">Tags</a></li>
                        <div class="indicator blue" style="z-index:1"></div>
                      </ul>
                    </div>
                    {features}
                    {components}
                    {team}
                    {suites}
                    {tags}
                </div>
               """.format(features=features_html, components=components_html, team=team_html,
                          suites=suites_html, tags=tags_html)

    @staticmethod
    def get_health_of_features(data):
        """
        :param data: LIST of DICTS aka
                     [{"category": "Feature A", "value": 95, "full": 100},
                      {"category": "Feature B", "value": 90, "full": 100}]
        :return: STRING, HTML for all the Health of Features chart
        """
        def css():

            return """
                    <style>
                        #health {
                            width: 100%;
                            height: 282px;
                        }
                    </style>
                   """

        def js():

            return """
                    <script>
                    $(document).ready(function() {
                        // Themes begin
                        am4core.useTheme(am4themes_dark);
                        am4core.useTheme(am4themes_animated);

                        // Create chart instance
                        var chart = am4core.create("health", am4charts.RadarChart);

                        // Add data
                        chart.data = {data};

                        // Make chart not full circle
                        chart.startAngle = -90;
                        chart.endAngle = 180;
                        chart.innerRadius = am4core.percent(20);

                        // Set number format
                        chart.numberFormatter.numberFormat = "#.#'%'";

                        // Create axes
                        var categoryAxis = chart.yAxes.push(new am4charts.CategoryAxis());
                        categoryAxis.dataFields.category = "category";
                        categoryAxis.renderer.grid.template.location = 0;
                        categoryAxis.renderer.grid.template.strokeOpacity = 0;
                        categoryAxis.renderer.labels.template.horizontalCenter = "right";
                        categoryAxis.renderer.labels.template.fontWeight = 500;
                        categoryAxis.renderer.labels.template.adapter.add("fill", function(fill, target) {
                          return (target.dataItem.index >= 0) ? chart.colors.getIndex(target.dataItem.index) : fill;
                        });
                        categoryAxis.renderer.minGridDistance = 10;

                        var valueAxis = chart.xAxes.push(new am4charts.ValueAxis());
                        valueAxis.renderer.grid.template.strokeOpacity = 0;
                        valueAxis.min = 0;
                        valueAxis.max = 100;
                        valueAxis.strictMinMax = true;

                        // Create series
                        var series1 = chart.series.push(new am4charts.RadarColumnSeries());
                        series1.dataFields.valueX = "full";
                        series1.dataFields.categoryY = "category";

                        series1.columns.template.fill = new am4core.InterfaceColorSet().getFor("alternativeBackground");
                        series1.columns.template.fillOpacity = 0.08;
                        series1.columns.template.cornerRadiusTopLeft = 20;
                        series1.columns.template.strokeWidth = 0;
                        series1.columns.template.radarColumn.cornerRadius = 20;

                        var series2 = chart.series.push(new am4charts.RadarColumnSeries());
                        series2.dataFields.valueX = "value";
                        series2.dataFields.categoryY = "category";
                        series2.clustered = false;
                        series2.columns.template.strokeWidth = 0;
                        series2.columns.template.tooltipText = "{category}: [bold]{value}%[/]";
                        series2.columns.template.radarColumn.cornerRadius = 20;

                        series2.columns.template.adapter.add("fill", function(fill, target) {
                          return chart.colors.getIndex(target.dataItem.index);
                        });

                        // Add cursor
                        chart.cursor = new am4charts.RadarCursor();
                    });
                    </script>
                   """.replace("{data}", str(data))

        return """
                <div class='col s12 m12 l6 xl6'>
                  <div class='card blue-grey darken-3'>
                    <div class='card-content white-text'>
                      <span class='card-title'>Health of Features:</span>
                      <div id="health"></div>
                      {css}
                      {js}
                    </div>
                  </div>
                </div>
               """.format(css=css(), js=js())

    @staticmethod
    def get_suggestions(data):

        def css():

            return """
                    <style>
                        #suggestions {
                            width: 100%;
                            height: 282px;
                        }
                    </style>
                   """

        def js():

            return """
                   <script>
                   </script>
                   """

        return """
                <div class="col s12 m12 l6 xl6">
                  <div class="card blue-grey darken-3">
                    <div class="card-content white-text">
                      <span class="card-title">Suggestions:</span>
                      <div id="suggestions">This feature is still in development</div>
                      {css}
                      {js}
                    </div>
                  </div>
                </div>
               """.format(css=css(), js=js())
