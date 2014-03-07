
angular.module('metrapp', ['ngRoute'])

.factory('Projects', function() {
  return [
  	{'id': 0,
  	 'name': 'metrapp0s',
  	 'description': 'awesome project for code fat monitoring',
  	 'site': 'http://codefat.lge.com'},
  	{'id': 1,
  	 'name': 'angularjs1', 
     'description': 'this is for future of the web',
     'site': 'http://angularjs.org'},
    {'id': 2,
     'name': 'angularjs2', 
     'description': 'this is for future of the web',
     'site': 'http://angularjs.org'}

  ];
})
 
.config(function($routeProvider) {
  $routeProvider
    .when('/', {
      controller:'ListCtrl',
      templateUrl:'static/partials/projects.html'
    })
    .when('/edit/:projectId', {
      controller:'EditCtrl',
      templateUrl:'static/partials/detail.html'
    })
    .when('/new', {
      controller:'CreateCtrl',
      templateUrl:'static/partials/detail.html'
    })
    .otherwise({
      redirectTo:'/'
    });
})
 
.controller('ListCtrl', function($scope, $http) {
  $http.get('api/projects').success(function(data) {
    console.log(data);
    $scope.summary = data['summary'];
    $scope.projects = data['projects'];
  });
})
 
.controller('CreateCtrl', function($scope, $location, $timeout, Projects) {
  $scope.save = function() {
    Projects.$add($scope.project, function() {
      $timeout(function() { $location.path('/'); });
    });
  };
})
 
.controller('EditCtrl',
  function($scope, $location, $routeParams, Projects) {
    $scope.projectId = $routeParams.projectId;
    $scope.projects = Projects;
    $scope.project = Projects[$routeParams.projectId];
    

    $scope.destroy = function() {
      delete $scope.projects[$scope.projectId];
      $location.path('/');
    };
 
    $scope.save = function() {
      //$scope.project.$save();
      $location.path('/');
    };
});