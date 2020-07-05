def insert_prefix_html():
    return """
    <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" type="text/css" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
            <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.21/css/dataTables.bootstrap.min.css">
			<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/searchpanes/1.1.1/css/searchPanes.dataTables.min.css">
			<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/select/1.3.1/css/select.dataTables.min.css">
        </head>
        <body style="text-align:center">

            <h1>LabCIF DOI: Image detections report</h1>
            <div style="width:70%;margin-left:auto;margin-right:auto">
                <table id="example" class="table table-striped table-bordered" style="width:100%;border-radius:8px">
                </table>
            </div>

        </body>
    """

def insert_suffix_html():
    return """
    <script src="https://code.jquery.com/jquery-3.5.1.min.js"></script>
    <script src="https://cdn.datatables.net/1.10.21/js/jquery.dataTables.min.js"></script>
	<script src="https://cdn.datatables.net/1.10.21/js/dataTables.bootstrap.min.js"></script>
	<script src="https://cdn.datatables.net/searchpanes/1.1.1/js/dataTables.searchPanes.min.js"></script>
	<script src="https://cdn.datatables.net/select/1.3.1/js/dataTables.select.min.js"></script>
    
    <script src="doi_report_data.js"></script>
    <script>
            $(document).ready(function() {
                $('#example').DataTable( {
                    searchPanes:{
						layout: 'columns-1'
					},
					dom: 'Pfrtilp',
                    data: dataSet,
                    deferRender: true,
                    columns: [
                        { title: "Detections Boxes" },
                        { title: "Original Image" },
                        { title: "File Name" },
                        { title: "File Size (KB)" },
                        { title: "Class" },
                        { title: "Best Confidence" },
                        { title: "File Case Path" }
                    ],
                    "columnDefs": [ 
                        {
                            "targets": [0, 1],
                            "searchable": false,
                            "orderable": false,
                        },
                        {
                            "targets" : [0, 1],
                            "render" : function ( url) {
                                return '<a href="' + url + '" target="_blank"><img height="60px" src="' + url + '"/></a>';
                            }
                        },
                        {
                            "targets" : [0, 1, 2, 3, 5, 6],
                            searchPanes:{
                                show: false,
                            },
                        },
                        {
                            "targets" : [4],
                            searchPanes:{
                                threshold: 0.99
                            },
                        }
                    ]
                } );
            } );
    </script>
        </html>"""