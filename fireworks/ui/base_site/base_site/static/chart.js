$(function () {
    $('#container').highcharts({
        chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false
        },
        title: {
            text: 'Current Activity'
        },
        tooltip: {
    	    pointFormat: '{series.name}: <b>{point.percentage:.2f}%</b>'
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: true,
                    color: '#000000',
                    connectorColor: '#000000',
                    format: '<b>{point.name}</b>: {point.percentage:.2f} %'
                }
            }
        },
        series: [{
            type: 'pie',
            name: 'Fireworks',
            data: [
                ['ARCHIVED', 943],
                ['DEFUSED', 921],
                ['COMPLETED', 164730],
                ['WAITING', 94866],
                ['READY', 25342],
                ['RESERVED', 981],
                ['FIZZLED', 63],
                ['RUNNING', 57]
            ]
        }]
    });
});

/** total = 287903 */
