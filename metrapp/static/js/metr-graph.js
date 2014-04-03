var metrGraph = angular.module('metrGraph',[])
metrGraph.directive('trend', function($window){
	function link(scope, element, attr) {
		var margin = {left:50,right:60,top:10,bottom:30};
		element.addClass('trend');

		var chart = d3.select(element[0])
				.style({width: "100%"})		
			.append('svg')
				.style({width: "100%",height: "100%"})
			.append("g")
			 	.attr("transform", "translate("+margin.left+","+margin.top+")");

		var xAxis = d3.svg.axis()
		    .orient("bottom");
		var yAxis = d3.svg.axis()
		    .orient("left");
		var y2Axis = d3.svg.axis()
		    .orient("right");

		var line = d3.svg.line();
		var line2 = d3.svg.line();

		var x = d3.time.scale();
		var y = d3.scale.linear();
		var y2 = d3.scale.linear();

		scope.data = [];
		//scope.since = new Date(new Date().getFullYear()-1, 0, 1);
		function draw() {
			var clientWidth = element[0].clientWidth;
			var clientHeight = clientWidth/3;
			var width = clientWidth - margin.left - margin.right;
			var height = clientHeight - margin.top - margin.bottom;

			d3.select(element[0]).style({height: clientHeight+"px"});

			chart.selectAll(".axis").remove();
			chart.selectAll("path").remove();

			var data = scope.data;
			if (scope.since) {
				data = data.filter(function(d){
					return d.date > scope.since;
				});
			}
			if (data.length == 0)
				return;

			var minDate = data[0].date;
			var maxDate = new Date();//data[data.length-1].date;

			x.range([0, width])
				.domain([minDate, maxDate]);
			y.range([height, 0])
				.domain(d3.extent(data, function(d) {return d.codefat; }));
			y2.range([height, 0])
				.domain(d3.extent(data, function(d) {return d.sloc; }));

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

		scope.$watch('data', function() {
			draw();
		},true);
		scope.$watch('since', function() {
			draw();
		});
		scope.$watch(function(){
			return element[0].clientWidth;
		}, function() {
			draw();
		});
		angular.element($window).bind('resize',function() {
			draw();
		});
	}
	return {
		restrict: 'E',
		link: link,
		scope: {'data': '=', 'since': '=' }
	};
});

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
		pie.sort(function(a,b){
			return b.no_commits - a.no_commits;
		});
		var arc = d3.svg.arc()
			.innerRadius(0)
			.outerRadius((min-margin) / 2);
		
		var g = svg.append('g').attr('transform', 'translate(' + width/2 + ', ' + height/2 + ')');
		var arcs = g.selectAll('path');

		scope.$watchCollection('data', update);

		function update() {
			console.log("update", scope.data);
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
