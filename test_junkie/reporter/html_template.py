from test_junkie.constants import TestCategory, Color, DocumentationLinks


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
                        <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.7.2/css/all.css" integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr" crossorigin="anonymous">
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
                            
                            .modal_absolute_value{{
                                font-size: 17px;
                            }}

                            .card:hover {{
                                background: #193746 !important;
                                transition: all .3s ease-in;
                            }}
                            
                            body {{
                                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
                            }}
                            
                            .success {{
                                background: #12d479;
                            }}
                            .fail {{
                                background: #fcd75f;
                            }}
                            .error {{
                                background: #ff7651;
                            }}
                            .ignore {{
                                background: #cce4eb;
                            }}
                            .skip {{
                                background: #34bff5;
                            }}
                            .cancel {{
                                background: #f19def;
                            }}
                            .info-badge {{
                                background: #aac7d2;
                            }}
                            
                            .parent-badge{{
                                margin-top: 8px;
                            }}
                            
                            .badge {{
                                border-radius: 3px;
                                margin-right: 7px;
                                color: #333 !important;
                            }}
                            
                            .traceback {{
                                background: #23323a !important;
                                padding: 15px !important;
                                color: #fd5858 !important;
                                margin: 0px !important;
                            }}
                            
                            .collapsible-header {{
                                background: #37474f !important;
                                border-color: #193746;
                            }}
                            
                            .collapsible.expandable {{
                                border: 1px #37474f;
                            }}
                            
                            .collapsible-header:hover {{
                                background: #193746 !important;
                                transition: all .3s ease-in;
                                transition: all .3s ease-out;
                            }}
                            
                            .collapsible-body {{
                                border-color: transparent;
                            }}
                            
                            .attempt-header {{
                                padding: 5px;
                                padding-bottom: 0px;
                                border: 0px;
                            }}
                            
                            .parameter {{
                              white-space: nowrap;
                              overflow: hidden;
                              text-overflow: ellipsis;
                              font-size: 14px;
                            }}
                            
                            html {{
                                overflow: scroll;
                                overflow-x: hidden;
                            }}
                            ::-webkit-scrollbar {{
                                width: 0px;  /* remove scrollbar space */
                                background: transparent;  /* optional: just make scrollbar invisible */
                            }}
                            /* optional: show position indicator in red */
                            ::-webkit-scrollbar-thumb {{
                                background: transparent;
                            }}
                            .traceback > textarea{{
                                padding-bottom: 0px;
                                margin-bottom: 0px;
                                overflow: auto;
                            }}
                            .large-data-card{{
                                width: 100%;
                                height: 370px;
                            }}
                        </style>
                        {body}
                        <script>
                            var database_lol = {database_lol}
                            function registerCopy(){{
                                $(".copy_icon").on("click", function(event){{
                                    event.stopPropagation();
                                    var copy_target = event.target.dataset.tcopy
                                    var data_element = document.getElementById(copy_target);
                                    if(data_element.tagName == "textarea") var val = data_element.value
                                    else var val = data_element.innerHTML
                                    
                                    var $temp = $("<input>");
                                    $("body").append($temp);
                                    $temp.val(val).select();
                                    document.execCommand("copy");
                                    $temp.remove();
                                    
                                    Materialize.toast('Copied!', 2000)
                                }});
                            }};
                        </script>
                    </body>
                </html> 
               """

    @staticmethod
    def get_donation_options():

        return """
                <div class="fixed-action-btn horizontal">
                    <a class="btn-floating btn-large waves-effect waves-light orange darken-4 modal-trigger" 
                    href="#developerModal"><i class="material-icons">favorite</i></a>
                </div>
                <script>
                    $(document).ready(function(){
                        $('#developerModal').modal();
                    });
                </script>
                <div id="developerModal" class="modal">
                    <div class="modal-content" style="color: black;">
                      <h4>Greetings!</h4>
                        <p>Some features are not yet finished. 
                           I'm <a rel="noopener" href="https://www.linkedin.com/in/arturspirin/" target="_blank">
                           Artur <i class='fas fa-external-link-alt'></i></a> by the way, the developer of
                           <a href="https://www.test-junkie.com/" target="_blank" rel="noopener">Test Junkie 
                           <i class='fas fa-external-link-alt'></i></a></p>
                        <p>It took a lot of effort, all my free time outside my day job, and many sleepless
                            nights to get this project to this point, that includes styling and doing data
                            processing in order to render all those charts and tables. I have been motivated by
                            the idea that it may become useful for testers, QA managers, QA team leads, and
                            even project managers and developers. Thus I open sourced it.</p>
                        <p>Ask yourself if all the effort I put in and the benefits Test Junkie brings to you
                            and/or your company (if any) are worth a donation or 2 minutes of your time.</p>
                        <p>Ways you can help:</p>
                        <ol>
                            <li>The biggest thing you can do for me is 
                                <a class="github-button" href="https://github.com/ArturSpirin/test_junkie" 
                                data-size="large" data-show-count="true" aria-label="Star ArturSpirin/test_junkie on 
                                GitHub">Star</a> the project on GitHub and share it on social media, with your friend 
                                and/or colleagues.</li>
                            <li>Write me a message on <a rel="noopener" href="https://www.linkedin.com/in/arturspirin/"
                                target="_blank">Linked In <i class='fas fa-external-link-alt'></i></a> and tell me 
                                about your experience with Test Junkie.</li>
                            <li>If you can afford, you can donate through
                                <a href="https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=FJPYWX5B776YS
                                &currency_code=USD&source=url" target="_blank" rel="noopener">PayPal 
                                <i class='fas fa-external-link-alt'></i></a>. Every penny donated motivates me more and 
                                more to spend time on this project.</li>
                            <li>You can also back me on
                                <a rel="noopener" href="https://www.patreon.com/join/arturspirin/" target="_blank">
                                Patreon <i class='fas fa-external-link-alt'></i></a> on behalf of your company and 
                                get some benefits by doing so.</li>
                        </ol>
                        <p>Happy testing!</p>
                    </div>
                    <div class="modal-footer">
                      <a href="#!" class="modal-close waves-effect waves-green btn-flat">Close</a>
                    </div>
                    <script async defer src="https://buttons.github.io/buttons.js"></script>
                </div>
               """

    @staticmethod
    def get_tiny_card_template(label, data, tooltip=None):
        return """
                    <div class="col s6 m4 l3 xl2">
                      <div class="card blue-grey darken-3 absolute_cards {tooltipped}" {tooltip}>
                        <div class="card-content white-text">
                          <span class="card-title">{label}</span>
                          <div class="absolute_value"><b>{data}</b></div>
                        </div>
                      </div>
                    </div>
                   """.format(label=label, data=data,
                              tooltip="data-html='true' data-tooltip='{}'".format(tooltip) if tooltip else "",
                              tooltipped="tooltipped"if tooltip else "")

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
                        .trace-label {
                            width: 120px;
                            background: #23323a;
                            color: #cac531;
                            position: relative;
                            padding: 3px;
                            padding-left: 8px;}
                        .trace-label:before {
                            content: '';
                            position: absolute;
                            top: 0; right: 0;
                            border-top: 28px solid #3c4f58;
                            border-left: 28px solid #23323a;
                            width: 0;}
                        .runtime-label {
                            width: 120px;
                            background: #23323a;
                            position: relative;
                            padding: 3px;
                            margin-bottom: 15px;
                            padding-right: 8px;}
                        .runtime-label:before {
                            content: '';
                            position: absolute;
                            top: 0; left: 0;
                            border-bottom: 28px solid #3c4f58;
                            border-right: 28px solid #23323a;
                            width: 0;}
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
                                        title: "Assignee" ,
                                        mDataProp: "assignee",
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
                                    row.setAttribute("href", "#testCaseModal")
                                    row.setAttribute('class', 'modal-trigger')
                                    row.setAttribute('data-test_id', data.test_id)
                                    row.setAttribute('data-suite_id', data.suite_id)
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
                                <table id="table_results" class="mdl-data-table" ></table>
                                {css}
                                {js}
                            </div>
                        </div>
                    </div>
                    
                    <div id="testCaseModal" class="modal" style="background-color: #3d4f58; color: #bbc3c7">
                        <div id="testCaseModalContent" class="modal-content">
                              <div class="row"><span style="font-size: 22px;" id="test_name"></span></div>
                              <div class="row" id="suite_metrics"></div>
                              <div class="row"><ul class="collapsible expandable" id="test_details"></ul></div>
                        </div>
                    </div>
                    <script>
                        $(document).ready(function(){{
                            $('#testCaseModal').modal();
                            var test_modal = $("#testCaseModal")
                            
                            function register_tr_clicks(){{
                                $("tr.modal-trigger").on("click", function(event){{
                                    var row = $(this)[0].dataset
                                    var test_id = row.test_id
                                    var suite_id = row.suite_id
                                    render_modal(test_id, suite_id)
                                }})
                            }}
                            
                            register_tr_clicks()
                            $("#table_results").on( 'draw.dt', function () {{
                                console.log("table redrawn")
                                register_tr_clicks()
                            }});

                            function render_modal(test_id, suite_id){{
                                var status = database_lol.tests[test_id]["status"]
                                var name = database_lol.tests[test_id]["name"]
                                var suite = database_lol.suites[suite_id]["name"]
                                var module = database_lol.suites[suite_id]["module"]
                                
                                $("#test_name").html("<span data-tooltip="+module+"."+suite+"."+name+"() class='tooltipped'><i class='material-icons'>near_me</i> <b>"+name+"()</b></span>")
                                
                                var suite_metrics_html = ""
                                var suite_metrics = database_lol.suites[suite_id].metrics
                                for(index in suite_metrics){{
                                    var data = suite_metrics[index]
                                    suite_metrics_html += '<div class="col s12 m6 l6 xl3">'                                
                                    suite_metrics_html += '<div class="card blue-grey darken-3 absolute_cards">'                                
                                    suite_metrics_html += '<div data-position="bottom" data-tooltip="This metrics show data for the entire suite: '+suite+' and not just for this test case" class="tooltipped card-content" style="color: #bbc3c7;">'
                                    suite_metrics_html += '<span>Performance</span>'                                
                                    suite_metrics_html += '<span class="card-title">@'+index+'</span>'                                
                                    suite_metrics_html += '<div class="modal_absolute_value">avg <b class="right">'+data.avg+'</b></div>'
                                    suite_metrics_html += '<div class="modal_absolute_value">median <b class="right">'+data.median+'</b></div>'
                                    suite_metrics_html += '<div class="modal_absolute_value">min <b class="right">'+data.minimum+'</b></div>'
                                    suite_metrics_html += '<div class="modal_absolute_value">max <b class="right">'+data.maximum+'</b></div>'
                                    suite_metrics_html += '<div class="modal_absolute_value">total <b class="right">'+data.total+'</b></div>'
                                    suite_metrics_html += '<div class="modal_absolute_value">executions <b class="right">'+data.executions+'</b></div>'
                                    suite_metrics_html += '<div class="modal_absolute_value">failures <b class="right">'+data.failures+'</b></div>'
                                    suite_metrics_html += '</div></div></div>'                                
                                }}
                                $("#suite_metrics").html(suite_metrics_html)
                                
                                var inject_html = ""
                                var data = database_lol.tests[test_id].metrics
                                var distinct_index = 0
                                
                                for(class_param in data){{
                                    var class_data = data[class_param]
                                    distinct_index += 1
                                    for(test_param in class_data){{
                                        distinct_index += 1
                                        
                                        var test_data = class_data[test_param]
                                        
                                        var actual_suite_param = test_data.class_param
                                        if(actual_suite_param == null) actual_suite_param = "N/A"
                                        else actual_suite_param = class_param
                                        
                                        var actual_test_param = test_data.param
                                        if(actual_test_param == null) actual_test_param = "N/A"
                                        else actual_test_param = test_param
                                        
                                        var status = test_data.status
                                        var retry = test_data.retry
                                        var params_total = test_data.params_total
                            
                                        var params_ul = '<li class="bg">'
                            
                                        params_ul += '<div class="collapsible-header bg">'
                                            params_ul += '<div class="col xl1 badge_value"><span class="badge '+status+'">'+status+'</span></div>'
                                            params_ul += '<div class="col xl1 badge_value"><span class="badge info-badge">'+params_total+'</span></div>'
                                            params_ul += '<div class="col xl10">'
                                                params_ul += '<div data-position="bottom" class="col xl6 parameter"><a data-tooltip="Copy class parameters" class="tooltipped waves-effect copy_icon"><i data-tcopy="suite_param_'+distinct_index+'" class="material-icons tiny right">content_copy</i></a>Class parameter: <b><span id="suite_param_'+distinct_index+'" class="tooltipped" data-tooltip="'+actual_suite_param+'">'+actual_suite_param+'</span></b></div>'
                                                params_ul += '<div data-position="bottom" class="col xl6 parameter"><a data-tooltip="Copy test parameters" class="tooltipped waves-effect copy_icon"><i data-tcopy="test_param_'+distinct_index+'" class="material-icons tiny right">content_copy</i></a>Test parameter: <b><span id="test_param_'+distinct_index+'" class="tooltipped" data-tooltip="'+actual_test_param+'">'+actual_test_param+'</span></b></div>'
                                            params_ul += '</div>'
                                        params_ul += '</div>'    
                                        
                                        params_ul += '<div class="collapsible-body">'
                                        
                                        var details_ul = '<ul class="collapsible expandable">'
                                        for(index in test_data.performance){{
                                            distinct_index += 1
                                            var attempt = parseInt(index) + 1
                                            
                                            var beforeTestTraceback = test_data.beforeTest.tracebacks[index]
                                            var afterTestTraceback = test_data.afterTest.tracebacks[index]
                                            var testTraceback = test_data.tracebacks[index]
                                            
                                            var beforeTestDuration = test_data.beforeTest.performance[index]
                                            var testDuration = test_data.performance[index]
                                            var afterTestDuration = test_data.afterTest.performance[index]
                                            
                                            var beforeTestStatus = "N/A"
                                            if(beforeTestTraceback == null && beforeTestDuration != null) beforeTestStatus = "OK"
                                            else if(beforeTestTraceback){{
                                                if(beforeTestTraceback.includes("AssertionError")) beforeTestStatus = "Fail"
                                                else beforeTestStatus = "Error"
                                            }}

                                            var afterTestStatus = "N/A"
                                            if(afterTestTraceback == null && afterTestDuration != null){{
                                                if (["N/A", "OK"].includes(beforeTestStatus)) afterTestStatus = "OK"
                                            }}
                                            else if(afterTestTraceback){{
                                                if(afterTestTraceback != afterTestStatus){{
                                                    if(afterTestTraceback.includes("AssertionError")) afterTestStatus = "Fail"
                                                    else afterTestStatus = "Error"
                                                }}
                                            }}
                                            
                                             var new_li = '<li>'
                                                new_li += '<div class="collapsible-header attempt-header">'
                                                    new_li += '<div class="col s1 m1 l1 xl1">'
                                                        new_li += '<i class="material-icons">fingerprint</i>'
                                                    new_li += '</div>'
                                                    new_li += '<div class="col s11 m11 l11 xl11">'
                                                        new_li += '<div class="col s3 m3 l3 xl3">'
                                                            new_li += '<span>Attempt: <span class="badge info-badge">'+attempt+'</span></span>'
                                                        new_li += '</div>'
                                                        new_li += '<div class="col s3 m3 l3 xl3">'
                                                            new_li += '<span>Runtime: <span data-position="bottom" class="badge info-badge">'+testDuration+'</span></span>'
                                                        new_li += '</div>'
                                                        new_li += '<div class="col s3 m3 l3 xl3">'
                                                            new_li += '<span>@beforeTest: <span class="badge info-badge">'+beforeTestStatus+'</span></span>'
                                                        new_li += '</div>'
                                                        new_li += '<div class="col s3 m3 l3 xl3">'
                                                            new_li += '<span>@afterTest: <span class="badge info-badge">'+afterTestStatus+'</span></span>'
                                                        new_li += '</div>'
                                                    new_li += '</div>'
                                                new_li += '</div>'
                                                
                                                if(beforeTestTraceback == null) beforeTestTraceback = "OK"
                                                if(testTraceback == null) testTraceback = "OK"
                                                if(afterTestTraceback == null) afterTestTraceback = "OK"
                                                new_li += '<div class="collapsible-body">'
                                                    var height = 150
                                                    var color = '#fd5858'
                                                    if(beforeTestTraceback == 'OK'){{
                                                        height = 40
                                                        color = '#10d478' 
                                                    }}
                                                    if(beforeTestDuration != null){{
                                                        new_li += '<div class="trace-label"><span>@beforeTest</span></div>'
                                                        new_li += '<div class="traceback"><textarea disabled style="overflow: auto; color: '+color+'; height: '+height+'px;" class="materialize-textarea">'+beforeTestTraceback+'</textarea></div>'
                                                        new_li += '<div class="right runtime-label"><span class="right">'+beforeTestDuration+'</span></div>'
                                                        new_li += '<br>'
                                                    }}
                                                    height = 150
                                                    color = '#fd5858'
                                                    if(testTraceback == 'OK'){{
                                                        height = 40
                                                        color = '#10d478' 
                                                    }}
                                                    new_li += '<div class="trace-label"><span>@test</span></div>'
                                                    new_li += '<div class="traceback"><textarea id="trace'+distinct_index+'" disabled style="overflow: auto; color: '+color+'; height: '+height+'px;" class="materialize-textarea">'+testTraceback+'</textarea></div>'
                                                    new_li += '<div class="right runtime-label"><span class="right">'+testDuration+'</span></div>'
                                                    new_li += '<br>'
                                                    height = 150
                                                    color = '#fd5858'
                                                    if(afterTestTraceback == 'OK'){{
                                                        height = 40
                                                        color = '#10d478' 
                                                    }}
                                                    if(afterTestDuration != null){{
                                                        new_li += '<div class="trace-label"><span>@afterTest</span></div>'
                                                        new_li += '<div class="traceback"><textarea disabled style="overflow: auto; color: '+color+'; height: '+height+'px;" class="materialize-textarea">'+afterTestTraceback+'</textarea></div>'
                                                        new_li += '<div class="right runtime-label"><span class="right">'+afterTestDuration+'</span></div>'
                                                        new_li += '<br>'
                                                    }}
                                                new_li += '</div>'
                                             new_li += '</li>'
                                             details_ul += new_li
                                        }}
                                        details_ul += '</ul>'
                                        params_ul += details_ul
                                        params_ul += '</div>'
                                        params_ul += '</li>'
                                        inject_html += params_ul
                                    }}
                                }}
                                $("#test_details").html(inject_html)
                                $('.collapsible.expandable').collapsible();
                                $('.tooltipped').tooltip();
                                registerCopy();
                            }}

                        }});
                    </script>
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
        doc_link = "<span>Resource monitoring disabled. See <a href=\"{link}\">documentation " \
                   "<i class='fas fa-external-link-alt'></i></a> to enabled it.</span>"\
                   .format(link=DocumentationLinks.HTML_REPORT)
        data = [] if data is None else data

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
                        for(dict in data) data[dict].date = new Date(data[dict].date)
                        
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
                    <div class='large-data-card card-content white-text'>
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
                    <div class="large-data-card card-content white-text">
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
        for status in TestCategory.ALL:
            series.append({"status": status, "label": status, "color": Color.MAPPING[status]})

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
                        categoryAxis_{chart_id}.renderer.labels.template.wrap = true;
                        categoryAxis_{chart_id}.renderer.labels.template.maxWidth = 120;
                        
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
                              series_{chart_id}.legendSettings.valueText = "{valueY}"
                            
                              // Make it stacked
                              series_{chart_id}.stacked = true;
                            
                              // Configure columns
                              series_{chart_id}.columns.template.width = am4core.percent(60);
                              series_{chart_id}.columns.template.tooltipText = "[bold]{name}[/]: {valueY}";
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
                        durationSeries_{chart_id}.legendSettings.valueText = "{valueY}"
                        
                        var bullet_{chart_id} = durationSeries_{chart_id}.bullets.push(new am4charts.Bullet());
                        var circle_{chart_id} = bullet_{chart_id}.createChild(am4core.Circle);
                        circle_{chart_id}.radius = 4;
                        circle_{chart_id}.fill = am4core.color("#fff");
                        circle_{chart_id}.strokeWidth = 3;
                        
                        // Legend
                        chart_{chart_id}.legend = new am4charts.Legend();
                        
                        // Add cursor
                        chart_{chart_id}.cursor = new am4charts.XYCursor();
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
                    <div class='large-data-card card-content white-text'>
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
                        #insights {
                            width: 100%;
                            height: 275px;
                            overflow-y: auto;
                        }
                        
                        #insights_list > li {
                            padding: 10px;
                        }
                        
                        #insights_list > li:hover {
                            background: #1e4254;
                            border-radius: 3px;
                        }
                        
                        .traceback-tooltip{
                            background-color: #eae8e8;
                            border-radius: 3px;
                            color: #444;
                            cursor: pointer;
                        }
                    </style>
                   """

        def js():

            return """
                   <script>
                       var insights = {data}
                       var insights_list = $("#insights_list")
                       var insights_html = ""
                       for(index in insights){{
                           insights_html += "<li>"+insights[index]+"</li>"
                       }}
                       insights_list.html(insights_html)
                   </script>
                   """

        return """
                <div class="col s12 m12 l6 xl6">
                  <div class="card blue-grey darken-3">
                    <div class="large-data-card card-content white-text">
                      <span class="card-title">Insights:</span>
                      <div id="insights">
                      <ul id="insights_list">
                      </ul>
                      </div>
                      {css}
                      {js}
                    </div>
                  </div>
                </div>
               """.format(css=css(), js=js().format(data=data))
