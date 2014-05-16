'use strict';

var app = angular.module('metrapp');

app.controller('ProjectListCtrl', ['$scope', 'ProjectList', function($scope, ProjectList) {
  $scope.variable = 'value';
  $scope.projects = ProjectList.projects;
  $scope.orderKey = 'codefat';
  $scope.reverseSort = true;
  $scope.sloc = 0;
  $scope.codefat = 0;
  $scope.$watch('projects.length', function() {
    var sloc = 0;
    var floc = 0;
    for (var i=0, sz=$scope.projects.length; i<sz; i++) {
      var p = $scope.projects[i];
      sloc += p.sloc;
      floc += p.floc;
    }
    $scope.sloc = sloc;
    if (sloc === 0) {
      $scope.codefat = 0;
    } else {
      $scope.codefat = 100 * floc/sloc;
    }
  });
  $scope.sortBy = function(key) {
    if ($scope.orderKey === key) {
      $scope.reverseSort = !$scope.reverseSort;
    } else {
      $scope.orderKey = key;
    }
  }
}]);

app.controller('FileCtrl', ['$scope', '$location', '$http', function($scope, $location, $http) {
  $scope.$watch(function(){
    return $location.search();
  }, update);
  update();
  function update() {
    $scope.context = $location.search();
    $http.get('/api/file', {'params' : $scope.context}).success(function(data){
      $scope.project = data.project;
      $scope.file = data.file;
      $scope.error = data.error;
    });
  }
}]);

app.controller('UserContributionController', ['$scope', '$http', function($scope, $http){
  $scope.lessLimit = 7;
  $scope.limit = $scope.lessLimit;
  $scope.showMoreToggle = function() {
    if ($scope.limit > $scope.lessLimit) {
      $scope.limit = $scope.lessLimit;
    } else {
      $scope.limit = $scope.users.length
    }
  };
  $scope.select = function(user) {
    $scope.selectedUser = user;
  }
  $http.get('/api/contribution?project_id=' + $scope.projectId).success(function(data){
    $scope.users = data.sort(function(a, b){
      return d3.descending(a.no_commits, b.no_commits);
    });
  });
}]);
