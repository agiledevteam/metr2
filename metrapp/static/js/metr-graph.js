var metrGraph = angular.module('metrGraph',[])
metrGraph.directive('trend', function(){
	function link(scope, element, attr) {
		var clientWidth = 600;
		var clientHeight = 300;
		var margin = {left:50,right:50,top:10,bottom:30};

		var width = clientWidth - margin.left - margin.right;
		var height = clientHeight - margin.top - margin.bottom;

		element.addClass('trend');

		var chart = d3.select(element[0])
				.style({width: clientWidth+"px", height: clientHeight+"px"})		
			.append('svg')
				.style({width: "100%",height: "100%"})
			.append("g")
			 	.attr("transform", "translate("+margin.left+","+margin.top+")");

		var x = d3.time.scale()
			.range([0, width]);
		var y = d3.scale.linear()
			.range([height, 0]);
		var y2 = d3.scale.linear()
			.range([height, 0]);

		var xAxis = d3.svg.axis()
		    .orient("bottom");
		var yAxis = d3.svg.axis()
		    .orient("left");
		var y2Axis = d3.svg.axis()
		    .orient("right");

		var line = d3.svg.line();
		var line2 = d3.svg.line();

		scope.data = [];
		scope.since = new Date(new Date().getFullYear()-1, 0, 1);
		function draw() {
			chart.selectAll(".axis").remove();
			chart.selectAll("path").remove();

			var data =
			 scope.data.filter(function(d){
				return d.date > scope.since;
			});

			if (data.length == 0)
				return;

			var minDate = data[0].date;
			var maxDate = data[data.length-1].date;

			x.domain([minDate, maxDate]);
			y.domain(d3.extent(data, function(d) {return d.codefat; }));
			y2.domain(d3.extent(data, function(d) {return d.sloc; }));

			xAxis.scale(x);
			yAxis.scale(y);
			y2Axis.scale(y2);

			line.x(function(d) { return x(d.date); })
				.y(function(d) { return y(d.codefat); });
			line2.x(function(d) { return x(d.date); })
			    .y(function(d) { return y2(d.sloc); });	

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
			// chart.selectAll(".y2.point")
			// 	.data(data)
			//   .enter().append("circle")
			//   	.attr("class", "y2 point")
			//   	.attr("cx", function(d){return x(d.date);})
			//   	.attr("cy", function(d){return y2(d.sloc);})
			//   	.attr("r", 2);
			// chart.selectAll(".y.point")
			// 	.data(data)
			//   .enter().append("circle")
			//   	.attr("class", "y point")
			//   	.attr("cx", function(d){return x(d.date);})
			//   	.attr("cy", function(d){return y(d.codefat);})
			//   	.attr("r", 2);
		}

		scope.$watchCollection(attr.dateData, function(data) {
			scope.data = data;
			draw();
		});
		// scope.$watch("since", function(since) {
		// 	console.log(since);
		// 	scope.since = since;
		// 	draw();
		// });
	}
	return {
		restrict: 'E',
		link: link
	};
});
	//     	$scope.margin = {top: 20, right: 75, bottom: 30, left: 50};
	//     	$scope.$watch('data.length', function(){
	//     		if ($scope.data.length > 0) {
	//     			$scope.draw();
	//     		}
	//     	});

	// 		function get_scale(data, margin) {
	// 			var chartElement = document.getElementById("chart");
	// 			var width = chartElement.clientWidth - margin.left - margin.right;
	// 			var height = chartElement.clientHeight - margin.top - margin.bottom;

	// 			var minDate = data[0].date;
	// 			var maxDate = data[data.length-1].date;
	// 			var x = d3.time.scale()
	// 				.range([0, width])
	// 				.domain([minDate, maxDate]);
	// 			var y = d3.scale.linear()
	// 				.range([height, 0])
	// 				.domain(d3.extent(data, function(d) {return d.codefat; }));
	// 			var y2 = d3.scale.linear()
	// 				.range([height, 0])
	// 				.domain(d3.extent(data, function(d) {return d.sloc; }));
	// 			var xAxis = d3.svg.axis()
	// 			    .scale(x)
	// 			    .orient("bottom");
	// 			var yAxis = d3.svg.axis()
	// 			    .scale(y)
	// 			    .orient("left");
	// 			var y2Axis = d3.svg.axis()
	// 			    .scale(y2)
	// 			    .orient("right");
	// 			var line = d3.svg.line()
	// 			    .x(function(d) { return x(d.date); })
	// 			    .y(function(d) { return y(d.codefat); });
	// 			var line2 = d3.svg.line()
	// 			    .x(function(d) { return x(d.date); })
	// 			    .y(function(d) { return y2(d.sloc); });
	// 			return {
	// 				'width': width, 'height': height,
	// 				'x': x, 'y': y, 'y2': y2,
	// 				'xAxis': xAxis, 'yAxis': yAxis, 'y2Axis': y2Axis,
	// 				'line': line, 'line2': line2
	// 			};
	// 		}
	// 		function getData() {
	// 			if ($scope.since)
	// 				return $scope.data.filter(function(d){return d.date > $scope.since;});
	// 			else
	// 				return $scope.data;
	// 		}
	//     	$scope.scale = function() {
	// 			var data = getData();
	// 			var margin = $scope.margin;

	// 			var scale = get_scale(data, margin);

	// 			var chart = d3.select(".chart").select("g");

	// 			chart.select(".x.axis")
	// 				.attr("transform", "translate(0," + scale.height + ")")
	// 				.call(scale.xAxis);
	// 			chart.select(".y2.axis")
	// 				.attr("transform", "translate(" + scale.width + ")")
	// 				.call(scale.y2Axis);
	// 			chart.select(".line")
	// 				.datum(data)
	// 				.attr("d", scale.line);
	// 			chart.select(".line2")
	// 				.datum(data)
	// 				.attr("d", scale.line2);

	// 			chart.selectAll(".y2.point")
	// 			  	.attr("cx", function(d){return scale.x(d.date);})
	// 			  	.attr("cy", function(d){return scale.y2(d.sloc);})
	// 			  	.attr("r", 2);
	// 			chart.selectAll(".y.point")
	// 			  	.attr("cx", function(d){return scale.x(d.date);})
	// 			  	.attr("cy", function(d){return scale.y(d.codefat);})
	// 			  	.attr("r", 2);
	// 		};
			
	// 		$scope.draw = function() {
	// 			var data = getData();
	// 			var margin = $scope.margin;
	// 			scope = $scope

	// 			var scale = get_scale(data, margin)

	// 			var chart = d3.select(".chart")
	// 			  .append("g")
	// 				.attr("transform", "translate("+margin.left+","+margin.top+")");

	// 			chart.append("g")
	// 				.attr("class", "x axis")
	// 				.attr("transform", "translate(0," + scale.height + ")")
	// 				.call(scale.xAxis);
	// 			chart.append("g")
	// 			    .attr("class", "y axis")
	// 			    .call(scale.yAxis);
	// 			chart.append("g")
	// 			    .attr("class", "y2 axis")
	// 			    .attr("transform", "translate(" + scale.width+ ")")
	// 			    .call(scale.y2Axis);

	// 			chart.append("path")
	// 				.datum(data)
	// 				.attr("class", "line2")
	// 				.attr("d", scale.line2);
	// 			chart.append("path")
	// 				.datum(data)
	// 				.attr("class", "line")
	// 				.attr("d", scale.line);

	// 			chart.selectAll(".y2.point")
	// 				.data(data)
	// 			  .enter().append("circle")
	// 			  	.attr("class", "y2 point")
	// 			  	.attr("cx", function(d){return scale.x(d.date);})
	// 			  	.attr("cy", function(d){return scale.y2(d.sloc);})
	// 			  	.attr("r", 2);
	// 			chart.selectAll(".y.point")
	// 				.data(data)
	// 			  .enter().append("circle")
	// 			  	.attr("class", "y point")
	// 			  	.attr("cx", function(d){return scale.x(d.date);})
	// 			  	.attr("cy", function(d){return scale.y(d.codefat);})
	// 			  	.attr("r", 2);
	// 		};
	// 	}
	// };

// 	return {
// 		restrict: 'E',
// 		scope: {data: '&'},
// 	    link: link
// 	};
// });

metrGraph.directive('pieChart', function() {
	function link(scope, element, attr) {
		var data = scope.data;
		var width = 250;
		var height = 250;
		var margin = 50;
		var svg = d3.select(element[0]).append('svg').style({width:width, height:height});
		
		var min = Math.min(width, height);

		var pie = d3.layout.pie();
		pie.value(function(d){
			return scope.getValue({d:d});
		});
		pie.sort(null);
		var arc = d3.svg.arc()
			.innerRadius(0)
			.outerRadius((min-margin) / 2);
		
		var g = svg.append('g').attr('transform', 'translate(' + width/2 + ', ' + height/2 + ')');
		var arcs = g.selectAll('path');

		scope.$watch('data', update, true);

		function update() {
			data = scope.data;
			if (!data) {return;}

			arcs = arcs.data(pie(data));
			arcs.exit().remove();
			arcs.enter().append('path')
			.style('fill', 'lightsteelblue')
			.style('stroke', 'white');
			//.style('opacity', function(d, i) { return Math.pow(0.8,i); });

			arcs.attr('d', arc);
			arcs.style('fill', function(d,i){
				if (d.data === scope.selected) {
					return 'steelblue';
				} else {
					return 'lightsteelblue';
				}
			});
			
		}

		scope.$watch('selected', function(){
			update();
		});

	}

	return {
		restrict: 'EA',
		scope: {data: '=', selected: '=', getValue: '&'},
		link: link
	};
});
