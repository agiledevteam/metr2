'use strict';

var app = angular.module('metrapp');

app.controller('ProjectListCtrl', ['$scope', 'ProjectList', function($scope, ProjectList) {
  $scope.variable = 'value';
  $scope.projects = ProjectList.projects;
  $scope.orderKey = 'codefat';
  $scope.reverseSort = true;
  $scope.codefat = function() {
    var sloc = 0;
    var floc = 0;
    for (var i=0, sz=$scope.projects.length; i<sz; i++) {
      var p = $scope.projects[i];
      sloc += p.sloc;
      floc += p.floc;
    }
    if (sloc === 0) {
      return 0;
    } else {
      return 100 * floc/sloc;
    }
  }
  $scope.sloc = function() {
    var sloc = 0;
    for (var i=0, sz=$scope.projects.length; i<sz; i++) {
      var p = $scope.projects[i];
      sloc += p.sloc;
    }
    return sloc;
  }
  $scope.sortBy = function(key) {
    if ($scope.orderKey === key) {
      $scope.reverseSort = !$scope.reverseSort;  
    } else {
      $scope.orderKey = key;  
    }
  }
}]);

