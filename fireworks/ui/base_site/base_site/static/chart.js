$(function() {

	$.getJSON('http://www.highcharts.com/samples/data/jsonp.php?filename=aapl-c.json&callback=?', function(data) {
		// Create the chart
		$('#container').highcharts('StockChart', {


			rangeSelector : {
				selected : 1
			},

			title : {
				text : 'Fireworks'
			},

			series : [{
				name : 'TOTAL',
				data : data,
				tooltip: {
					valueDecimals: 2
				}
			}]
		});
	});

});