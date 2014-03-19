angular.module('metrGraph',[]).
directive('trend', function(){
	return {
		restrict: 'E',
		scope: {
			data: '=',
			since: '=?',
		},
	    templateUrl: '/static/partials/trend.html',
	    controller: function($scope, $window) {
	    	$scope.margin = {top: 20, right: 75, bottom: 30, left: 50};
	    	$scope.$watch('data.length', function(){
	    		if ($scope.data.length > 0) {
	    			$scope.draw();
	    		}
	    	});
			angular.element($window).bind('resize',function(){
				$scope.scale();
			});
			function get_scale(data, margin) {
				var chartElement = document.getElementById("chart");
				var width = chartElement.clientWidth - margin.left - margin.right;
				var height = chartElement.clientHeight - margin.top - margin.bottom;

				var minDate = data[0].date;
				var maxDate = data[data.length-1].date;
				var x = d3.time.scale()
					.range([0, width])
					.domain([minDate, maxDate]);
				var y = d3.scale.linear()
					.range([height, 0])
					.domain(d3.extent(data, function(d) {return d.codefat; }));
				var y2 = d3.scale.linear()
					.range([height, 0])
					.domain(d3.extent(data, function(d) {return d.sloc; }));
				var xAxis = d3.svg.axis()
				    .scale(x)
				    .orient("bottom");
				var yAxis = d3.svg.axis()
				    .scale(y)
				    .orient("left");
				var y2Axis = d3.svg.axis()
				    .scale(y2)
				    .orient("right");
				var line = d3.svg.line()
				    .x(function(d) { return x(d.date); })
				    .y(function(d) { return y(d.codefat); });
				var line2 = d3.svg.line()
				    .x(function(d) { return x(d.date); })
				    .y(function(d) { return y2(d.sloc); });
				return {
					'width': width, 'height': height,
					'x': x, 'y': y, 'y2': y2,
					'xAxis': xAxis, 'yAxis': yAxis, 'y2Axis': y2Axis,
					'line': line, 'line2': line2
				};
			}
			function getData() {
				if ($scope.since)
					return $scope.data.filter(function(d){return d.date > $scope.since;});
				else
					return $scope.data;
			}
	    	$scope.scale = function() {
				var data = getData();
				var margin = $scope.margin;

				var scale = get_scale(data, margin);

				var chart = d3.select(".chart").select("g");

				chart.select(".x.axis")
					.attr("transform", "translate(0," + scale.height + ")")
					.call(scale.xAxis);
				chart.select(".y2.axis")
					.attr("transform", "translate(" + scale.width + ")")
					.call(scale.y2Axis);
				chart.select(".line")
					.datum(data)
					.attr("d", scale.line);
				chart.select(".line2")
					.datum(data)
					.attr("d", scale.line2);

				chart.selectAll(".y2.point")
				  	.attr("cx", function(d){return scale.x(d.date);})
				  	.attr("cy", function(d){return scale.y2(d.sloc);})
				  	.attr("r", 2);
				chart.selectAll(".y.point")
				  	.attr("cx", function(d){return scale.x(d.date);})
				  	.attr("cy", function(d){return scale.y(d.codefat);})
				  	.attr("r", 2);
			};
			
			$scope.draw = function() {
				var data = getData();
				var margin = $scope.margin;
				scope = $scope

				var scale = get_scale(data, margin)

				var chart = d3.select(".chart")
				  .append("g")
					.attr("transform", "translate("+margin.left+","+margin.top+")");

				chart.append("g")
					.attr("class", "x axis")
					.attr("transform", "translate(0," + scale.height + ")")
					.call(scale.xAxis);
				chart.append("g")
				    .attr("class", "y axis")
				    .call(scale.yAxis);
				chart.append("g")
				    .attr("class", "y2 axis")
				    .attr("transform", "translate(" + scale.width+ ")")
				    .call(scale.y2Axis);

				chart.append("path")
					.datum(data)
					.attr("class", "line2")
					.attr("d", scale.line2);
				chart.append("path")
					.datum(data)
					.attr("class", "line")
					.attr("d", scale.line);

				chart.selectAll(".y2.point")
					.data(data)
				  .enter().append("circle")
				  	.attr("class", "y2 point")
				  	.attr("cx", function(d){return scale.x(d.date);})
				  	.attr("cy", function(d){return scale.y2(d.sloc);})
				  	.attr("r", 2);
				chart.selectAll(".y.point")
					.data(data)
				  .enter().append("circle")
				  	.attr("class", "y point")
				  	.attr("cx", function(d){return scale.x(d.date);})
				  	.attr("cy", function(d){return scale.y(d.codefat);})
				  	.attr("r", 2);
			};
		}
	};
});