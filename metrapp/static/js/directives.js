var app = angular.module('metrapp');

app.directive('userProfile', function(){
	function link(scope, element, attr) {
		function update() {
			d3.select(element[0]).select('svg').remove();
			var data = scope.data;
			if (!data) {
				return;
			}

			var width = 250;
			var height = 250;
			var margin = 20;

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

			var xAxis = d3.svg.axis().scale(x).innerTickSize(3);
			var yAxis = d3.svg.axis().scale(y).orient("left").innerTickSize(3);

			svg.selectAll("circle")
				.data(data)
				.enter().append("circle")
				.attr("r", 3)
				.attr("cx", function(d){return x(d.delta_sloc)})
				.attr("cy", function(d){return y(d.delta_floc)});
			svg.append("g")
				.attr("class", "x axis")
				.call(xAxis);
			svg.append("g")
				.attr("class", "y axis")
				//.attr('transform', 'rotate(90)')
				.call(yAxis);
		}
		scope.$watch('data', update);
	}
	return {
		restrict: 'E',
		scope: {data: '='},
		link: link
	};
});

app.directive('inlinePie', function() {
	function link(scope, element, attr) {
		scope.$watchCollection(attr.data, function(data) {
			for (var v in data) {
				if (!data[v]) {
					return;
				}
			}
			$(element[0]).text(data.join("/")).peity("pie").change()
		});
	}
	return {
		restrict: 'A',
		link: link,
	};
});
