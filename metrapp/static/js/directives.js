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

		var dx = 2;
		var dy = 2;

	  var colorRange = ['#eee', '#d6e685', '#8cc665', '#44a340', '#1e6823'];
		var timestamp = scope.timestamp;

		var seconds = 60 * 60 * 24;
		var milliseconds = 1000 * seconds;
		var days = d3.range(366).map(function(){return 0;});
		var firstDay = new Date();
		firstDay.setDate(firstDay.getDate() - days.length);
		firstDay = new Date(firstDay.toDateString());

		var offset = firstDay.getDay();

		scope.$watchCollection("data", update);
		function update() {
			if (!scope.data)
				return;
			days = days.map(function(){return 0;});
			scope.data.forEach(function(each){
				var time = new Date(timestamp(each) * 1000);
				if (time > firstDay) {
					var day = Math.floor((time.getTime() - firstDay.getTime()) / milliseconds);
					days[day] += 1;
				}
			});

			var color = d3.scale.linear()
				.domain([0, 1, 3, 5, d3.max(days)])
				.range(colorRange);

			var cells = calendar
				.selectAll('rect')
				.data(days);
			cells.transition()
					.style('fill', function(d){
						return color(d);
					});
		}

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

		calendar.selectAll('rect')
			.data(days)
			.enter().append('rect')
			.attr({width: x, height: y})
			.attr("x", function(d, i){
				return Math.floor((offset + i) / 7) * (x + dx);
			})
			.attr("y", function(d, i){
				return ((offset + i) % 7) * (y + dy);
			})
			.style('fill', colorRange[0]);
		calendar.selectAll('text.wday')
			.data(dayOfWeekLabel).enter().append('text').attr('class', 'wday')
			.text(function(d){ return d.title;})
			.style("display", function(d){
				return d.style.display;
			})
			.attr('text-anchor', 'middle')
			.attr('dx', -10)
			.attr('dy', function(d,i){ return 9 + (y+dy)*i;});
	}
	return {
		link: link,
		scope: {data: '=', timestamp: '&'}
	};
});

app.directive('syntaxHighlighter', function() {
	function link(scope, element) {
		scope.$watch('file', function(data) {
			if (!data)
				return;
			element.html('<pre class="brush: java"></pre>');
			element.find('pre').text(data);
			var pre = element.children()[0];
			SyntaxHighlighter.highlight(pre);
		})
	}
	return {
		restrict: 'E',
		link: link,
		replace: true,
		scope: {
			file: '='
		}
	};
});

app.directive('metrStat', function() {
	return {
		restrict: 'E',
		scope: {
			data: '='
		},
		template: '<ul class="list-inline summary">\n\
	        <li class="sloc">SLOC <span class="num">{{data.sloc|number}}</span></li>\n\
	        <li class="floc">FLOC <span class="num">{{data.floc|number:2}}</span></li>\n\
	        <li class="codefat">Code Fat <span class="num">{{data.codefat|number:2}}%</span></li>\n\
	      </ul>'
	};
});


app.directive('myTabs', function() {
	return {
		restrict: 'E',
		transclude: true,
		scope: {},
		controller: function($scope) {
			var panes = $scope.panes = [];

			$scope.select = function(pane) {
				angular.forEach(panes, function(pane) {
					pane.selected = false;
				});
				pane.selected = true;
			};

			this.addPane = function(pane) {
				if (panes.length === 0) {
					$scope.select(pane);
				}
				panes.push(pane);
			};
		},
		templateUrl: 'static/partials/my-tabs.html'
	};
});

app.directive('myPane', function() {
	return {
		require: '^myTabs',
		restrict: 'E',
		transclude: true,
		scope: {
			title: '@'
		},
		link: function(scope, element, attrs, tabsCtrl) {
			tabsCtrl.addPane(scope);
		},
		templateUrl: 'static/partials/my-pane.html'
	};
});