
angular.module('metrapp', ['metrGraph', 'metrServices', 'ngRoute', 'ui.bootstrap', 'ui.bootstrap.pagination'])

 
.config(function($routeProvider) {
  $routeProvider
    .when('/', {
      controller:'OverviewCtrl',
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
    .when('/users/', {
      controller:'UsersCtrl',
      templateUrl:'static/partials/users.html'
    })
    .when('/user/:userId', {
      controller:'UserCtrl',
      templateUrl:'static/partials/user.html'
    })
    .when('/diff', {
      controller:'DiffCtrl',
      templateUrl:'static/partials/diff.html'
    })
    .otherwise({
      redirectTo:'/'
    });
})
 
.controller('OverviewCtrl', ['$scope', '$http', function($scope, $http) {
  $scope.data = [];
  $scope.since = new Date(new Date().getFullYear(), 0, 1);
  $http.get('/api/daily').success(function(data){
    $scope.data = data.map(function(d){
      d.date = new Date(d.date);
      return d;
    });
  });
}])
 
.controller('ProjectCtrl', ['$scope', '$routeParams', '$http', function($scope, $routeParams, $http) {
  initPagination($scope);
  $scope.projectId = $routeParams.projectId;
  $scope.data = [];
  $scope.since = new Date(new Date().getFullYear(), 0, 1);
  $http.get('/api/daily?project_id=' + $scope.projectId).success(function(data){
    $scope.data = data.map(function(d){
      d.date = new Date(d.date);
      return d;
    });
  });
  $http.get('api/project/' + $scope.projectId).success(function(data) {
    $scope.project = data['project'];
    $scope.summary = data['summary'];
    $scope.commits = data['commits'];
  });

}])

.controller('CommitCtrl', function($scope, $routeParams, $http) {
  $http.get('api/commit/' + $routeParams.projectId + '/' + $routeParams.commitId).success(function(data) {
    $scope.project = data['project'];
    $scope.commit = data['commit'];
    $scope.diffs = data['diffs'];
  });
  $scope.url_for = function(diff) {
    return buildUrl('#/diff', {
      'projectId': $scope.project.id,
      'filename': diff.new.filename,
      'commitId': $scope.commit.sha1,
      'fileId': diff.new.sha1,
      'parentFileId': diff.old.sha1
    });
  };
})

.controller('DiffCtrl', function($scope, $routeParams, $http) {
  var url = 'api/diff/' + $routeParams.projectId + '/'
    + $routeParams.commitId + '/'
    + $routeParams.parentFileId + '/'
    + $routeParams.fileId;
  $http.get(url).success(function(data) {
    $scope.lines = data['lines'];
  });
})

.controller('UsersCtrl', function($scope, $http) {
  initPagination($scope);
  $http.get('api/users').success(function(data) {
    $scope.users = data['users'];
  });
})

.controller('UserCtrl', function($scope, $routeParams, $http) {
  initPagination($scope);
  $http.get('api/user/' + $routeParams.userId).success(function(data) {
    $scope.user = data['user'];
    $scope.commits = data['commits']
  });
})

.filter('page', function() {
    return function(array, currentPage, pageSize) {
      var start = (currentPage-1) * pageSize;
      var end = currentPage * pageSize
      return array.slice(start, end);
    }
});

function initPagination($scope) {
  $scope.currentPage = 1;
  $scope.pageSize = 20;
  $scope.pageStart = 1;
  $scope.$watch('currentPage', function() {
    $scope.pageStart = 1 + ($scope.currentPage - 1) * $scope.pageSize;
  });

}

function buildUrl(url, parameters){
  var qs = "";
  for(var key in parameters) {
    var value = parameters[key];
    qs += encodeURIComponent(key) + "=" + encodeURIComponent(value) + "&";
  }
  if (qs.length > 0){
    qs = qs.substring(0, qs.length-1); //chop off last "&"
    url = url + "?" + qs;
  }
  return url;
}