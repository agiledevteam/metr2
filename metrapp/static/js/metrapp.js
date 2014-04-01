
angular.module('metrapp', [
  'metrGraph', 
  'metrServices', 
  'ngRoute',
  'ngSanitize',
  'ui.bootstrap', 
  'ui.bootstrap.pagination'])

 
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
  $scope.since = new Date(new Date().getFullYear()-1, 0, 1);
  $http.get('api/project/' + $scope.projectId).success(function(data) {
    $scope.project = data['project'];
  });
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
  $scope.$watch("project.branch", function(newBranch) {
    if (!newBranch)
      return;
    var queryParams = 'project_id=' + $scope.projectId + '&branch=' + newBranch;
    $http.get('api/commits?' + queryParams).success(function(commits) {
      $scope.commits = commits;
      if (commits.length > 0) {
        $scope.summary = commits[0];
        $scope.data = commits
          .filter(function(c){return c.sloc>0;})
          .map(function(c){return {
            date: new Date(c.timestamp*1000),
            codefat: c.codefat,
            sloc: c.sloc
          };})
          .sort(function(a,b){return d3.ascending(a.date, b.date);});
        $scope.users = d3.nest()
          .key(function(d){return d.author;})
          .entries(commits)
          .map(function(group){
            return {
                author: group.key,
                no_commits: group.values.length,
                delta_sloc: d3.sum(group.values, function(d){return d.delta_sloc;}),
                delta_floc: d3.sum(group.values, function(d){return d.delta_floc;})
            }; 
          });
      } else {
        $scope.data = [];
        $scope.summary = {};
        $scope.users = [];
      }
    });
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
  $http.get('api/user2?author=' + $routeParams.userId).success(function(data) {
    $scope.user = data['user'];
    $scope.commits = data['commits']
  });
})

.filter('shorten', function() {
  return function(title) {
    // if title starts with [..] tags
    return title.replace(/^(\[.*\])(.*)/, '<small title="$1">[..]</small>$2');
  }
})
.filter('page', function() {
  return function(array, currentPage, pageSize) {
    if (array instanceof Array) {
      var start = (currentPage-1) * pageSize;
      var end = currentPage * pageSize
      return array.slice(start, end);      
    } else {
      return [];
    }
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