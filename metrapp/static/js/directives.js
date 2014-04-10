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
		link: link
	};
});

app.directive('calendarGraph', function() {
	function link(scope, element, attr) {
		var x = 11;
		var y = 11;
		var days = 365;
		var dx = 2;
		var dy = 2;

		var day = new Date();
		day.setDate(day.getDate() - days - 1);
		day.setDate(day.getDate() - day.getDay());

		var weeks = d3.range(Math.floor((days + 1) / 7));
		console.log(weeks);
		var days = d3.range(7);

		var calendar = d3.select(element[0])
				.attr('class', 'calendar-graph')
				.style('display', 'inline-block')
				.attr({width: '721px', height: '110px'})
			.append('div').append('svg')
				.attr({width: '721px', height: '110px'})
			.append('g')
				.attr('transform', 'translate(20,20)');

		var legend = d3.select(element[0]).append('div').attr('class', 'activity-legend');
		legend.append('span').text("Less");
		legend.append('ul').attr('class', 'legend')
			.selectAll('li')
			.data(['#eee', '#d6e685', '#8cc665', '#44a340', '#1e6823'])
			.enter().append('li').style('background-color', function(d){return d;});
		legend.append('span').text("More");

		var dayOfWeekLabel = [{title:'S', style:{display:'none'}}
			,{title:'M', style:{}}
			,{title:'T', style:{display:'none'}}
			,{title:'W', style:{}}
			,{title:'T', style:{display:'none'}}
			,{title:'F', style:{}}
			,{title:'S', style:{display:'none'}}];
		calendar
			.selectAll('g')
			.data(weeks).enter().append('g')
				.attr('transform', function(d, i) {
					return 'translate(' + (i*(x + dx))+ ')';
				}).selectAll('rect')
					.data(days).enter().append('rect')
						.style('fill', '#eee')
						.attr({width: x, height: y})
						.attr("y", function(d,i){
							return i*(y + dy);
						});
		calendar.selectAll('text.wday')
			.data(dayOfWeekLabel).enter().append('text').attr('class', 'wday')
			.text(function(d){ return d.title;})
			.style("display", function(d){
				return d.style.display;
			})
			.attr('text-anchor', 'middle')
			.attr('dx', -10)
			.attr('dy', function(d,i){ return 9 + (y+dy)*i;});

		var week = 0;
		for (var i=0; i<366; i++) {

			day.setDate(day.getDate() + 1);
			if (day.getDay() == 6)
				week++;
		}
	}
	return {
		link: link,
	};
});
