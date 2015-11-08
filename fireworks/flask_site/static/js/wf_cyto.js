$(document).ready(function() {
    var options = {
         name: 'dagre',

          // dagre algo options, uses default value on undefined
         nodeSep: undefined, // the separation between adjacent nodes in the same rank
         edgeSep: undefined, // the separation between adjacent edges in the same rank
         rankSep: undefined, // the separation between adjacent nodes in the same rank
         rankDir: 'TB', // 'TB' for top to bottom flow, 'LR' for left to right
         minLen: function( edge ){ return 1; }, // number of ranks to keep between the source and target of the edge
         edgeWeight: function( edge ){ return 1; }, // higher weight edges are generally made shorter and straighter than lower weight edges

         // general layout options
         fit: true, // whether to fit to viewport
         padding: 30, // fit padding
         animate: false, // whether to transition the node positions
         animationDuration: 500, // duration of animation in ms if enabled
         boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
         ready: function(){}, // on layoutready
         stop: function(){} // on layoutstop
};
       $.getJSON("/wf/"+ $("#wf_id").html()+ "/json", function(result){
        var cy = cytoscape({
container: document.getElementById('cy'),
style: cytoscape.stylesheet()
    .selector('node')
    .css({
    'content': 'data(name)',
    'text-valign': 'center',
    'width':'data(width)',
    'shape':'rectangle',
    'color': 'white',
    'background-color' : 'data(state)',
    'text-outline-width': 1,
    'font-family': "Open Sans, sans-serif",
    'font-size': 14,
    'text-outline-color': '#888'
    })
    .selector('edge')
    .css({
    'target-arrow-shape': 'triangle'
    })
    .selector(':selected')
    .css({
    'background-color': 'black',
    'line-color': 'black',
    'target-arrow-color': 'black',
                       'source-arrow-color': 'black'
                                   })
    .selector('.faded')
    .css({
    'opacity': 0.25,
    'text-opacity': 0
           }),
    elements: {
    nodes:result.nodes,
    edges:result.edges,
      },
    ready: function() {
               window.cy = this;
               cy.layout(options);
               cy.panzoom();
           }
});
 $('#json').JSONView('collapse')
var source = $("#job-details").html();
var template = Handlebars.compile(source);
cy.on("click", 'node', function(evt) {
        $.getJSON("/fw/" + this.data('id') + "/details", function(result) {
                $("#job-details-target").html(template(result));
            });
        });

});




});


