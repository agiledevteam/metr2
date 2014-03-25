var app = angular.module('metrapp');

app.directive('userProfile', function(){
	function link(scope, element, attr) {
		var data = scope.data;

		var width = 250;
		var height = 250;
		var margin = 50;

		var svg = d3.select(element[0]).append('svg')
			.style({width: width, height: height})
			.append('g')
			.attr('transform', 'translate(' + width/2 + ',' + height/2+ ')');
		
		var x_extent = d3.extent(data, function(d){return d.delta_sloc;});
		var y_extent = d3.extent(data, function(d){return d.delta_floc;});
		var max = d3.max(x_extent.concat(y_extent).map(Math.abs))
		
		var x = d3.scale.linear()
			.domain([-max, max])
			.range([-(width-margin)/2, (width-margin)/2]);
		var y = d3.scale.linear()
			.domain([-max, max])
			.range([(height-margin)/2, -(height-margin)/2]);

		svg.selectAll("circle")
			.data(data)
			.enter().append("circle")
			.attr("r", 3)
			.attr("cx", function(d){return x(d.delta_sloc)})
			.attr("cy", function(d){return y(d.delta_floc)});
		console.log(data);
	}
	return {
		restrict: 'E',
		scope: {data: '='},
		link: link
	};
});