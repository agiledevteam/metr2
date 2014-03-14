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

