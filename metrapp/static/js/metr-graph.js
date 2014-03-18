angular.module('metrGraph',[]).
directive('trend', function(){
	return {
		restrict: 'E',
		scope: {
			data: '=data'
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
	    	$scope.scale = function() {
				var data = $scope.data;
				var margin = $scope.margin;

				var chartElement = document.getElementById("chart");
				var width = chartElement.clientWidth - margin.left - margin.right;
				var height = chartElement.clientHeight - margin.top - margin.bottom;

				var x = d3.scale.linear()
					.range([0, width])
					.domain(d3.extent(data, function(d) { return d[0]; }));
				var y = d3.scale.linear()
					.range([height, 0])
					.domain(d3.extent(data, function(d) {return d[1]; }));
				var y2 = d3.scale.linear()
					.range([height, 0])
					.domain(d3.extent(data, function(d) {return d[2]; }));
				var xAxis = d3.svg.axis()
				    .scale(x)
				    .orient("bottom");
				var yAxis = d3.svg.axis()
				    .scale(y)
				    .orient("left");
				var y2Axis = d3.svg.axis()
				    .scale(y2)
				    .orient("right");

				var chart = d3.select(".chart").select("g");

				chart.select(".x.axis")
					.attr("transform", "translate(0," + height + ")")
					.call(xAxis);
				chart.select(".y2.axis")
					.attr("transform", "translate(" + width + ")")
					.call(y2Axis);
				var line = d3.svg.line()
				    .x(function(d) { return x(d[0]); })
				    .y(function(d) { return y(d[1]); });
				var line2 = d3.svg.line()
				    .x(function(d) { return x(d[0]); })
				    .y(function(d) { return y2(d[2]); });
				chart.select(".line")
					.datum(data)
					.attr("d", line);
				chart.select(".line2")
					.datum(data)
					.attr("d", line2);

				chart.selectAll(".y2.point")
				  	.attr("cx", function(d){return x(d[0]);})
				  	.attr("cy", function(d){return y2(d[2]);})
				  	.attr("r", 2);
				chart.selectAll(".y.point")
				  	.attr("cx", function(d){return x(d[0]);})
				  	.attr("cy", function(d){return y(d[1]);})
				  	.attr("r", 2);
			};
			$scope.draw = function() {
				var data = $scope.data;
				var margin = $scope.margin;

				var chartElement = document.getElementById("chart");
				var width = chartElement.clientWidth - margin.left - margin.right;
				var height = chartElement.clientHeight - margin.top - margin.bottom;

				var x = d3.scale.linear()
					.range([0, width])
					.domain(d3.extent(data, function(d) { return d[0]; }));
				var y = d3.scale.linear()
					.range([height, 0])
					.domain(d3.extent(data, function(d) {return d[1]; }));
				var y2 = d3.scale.linear()
					.range([height, 0])
					.domain(d3.extent(data, function(d) {return d[2]; }));


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
				    .x(function(d) { return x(d[0]); })
				    .y(function(d) { return y(d[1]); });
				var line2 = d3.svg.line()
				    .x(function(d) { return x(d[0]); })
				    .y(function(d) { return y2(d[2]); });

				var chart = d3.select(".chart")
				  .append("g")
					.attr("transform", "translate("+margin.left+","+margin.top+")");

				chart.append("g")
					.attr("class", "x axis")
					.attr("transform", "translate(0," + height + ")")
					.call(xAxis);
				chart.append("g")
				    .attr("class", "y axis")
				    .call(yAxis);
				chart.append("g")
				    .attr("class", "y2 axis")
				    .attr("transform", "translate(" + width+ ")")
				    .call(y2Axis);

				chart.append("path")
					.datum(data)
					.attr("class", "line2")
					.attr("d", line2);
				chart.append("path")
					.datum(data)
					.attr("class", "line")
					.attr("d", line);

				chart.selectAll(".y2.point")
					.data(data)
				  .enter().append("circle")
				  	.attr("class", "y2 point")
				  	.attr("cx", function(d){return x(d[0]);})
				  	.attr("cy", function(d){return y2(d[2]);})
				  	.attr("r", 2);
				chart.selectAll(".y.point")
					.data(data)
				  .enter().append("circle")
				  	.attr("class", "y point")
				  	.attr("cx", function(d){return x(d[0]);})
				  	.attr("cy", function(d){return y(d[1]);})
				  	.attr("r", 2);
			};
		}
	};
});