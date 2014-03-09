
angular.module('metrapp', ['ngRoute'])

 
.config(function($routeProvider) {
  $routeProvider
    .when('/', {
      controller:'ListCtrl',
      templateUrl:'static/partials/projects.html'
    })
    .when('/project/:projectId', {
      controller:'ProjectCtrl',
      templateUrl:'static/partials/project.html'
    })
    .when('/commit/:projectId/:commitId', {
      controller:'CommitCtrl',
      templateUrl:'static/partials/commit.html'
    })
    .otherwise({
      redirectTo:'/'
    });
})
 
.controller('ListCtrl', function($scope, $http) {
  $http.get('api/projects').success(function(data) {
    $scope.summary = data['summary'];
    $scope.projects = data['projects'];
  });
})
 
.controller('ProjectCtrl', function($scope, $routeParams, $http) {
  $http.get('api/project/' + $routeParams.projectId).success(function(data) {
    $scope.project = data['project'];
    $scope.summary = data['summary'];
    $scope.commits = data['commits'];
  });
})

.controller('CommitCtrl', function($scope, $routeParams, $http) {
  $http.get('api/commit/' + $routeParams.projectId + '/' + $routeParams.commitId).success(function(data) {
    $scope.project = data['project'];
    $scope.commit = data['commit'];
    $scope.diffs = data['diffs'];
  });
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