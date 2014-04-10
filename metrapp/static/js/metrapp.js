
Date.prototype.addMonths = function(m) {
  var result = new Date(this);
  result.setMonth(this.getMonth() + m);
  return result;
};

angular.module('metrapp', [
  'metrGraph',
  'metrServices',
  'ngSanitize',
  'ui.bootstrap',
  'ui.bootstrap.pagination'])

.controller('MainCtrl', ['$scope', '$location', function($scope, $location) {
  $scope.$watch(function(){
    return $location.path();
  }, function() {
    $scope.page = $location.path().split("/")[1];
  });
}])

.controller('OverviewCtrl', ['$scope', '$http', function($scope, $http) {
  $scope.data = [];
  $scope.durations = [{
    title: 'this year',
    since: new Date(new Date().getFullYear(), 0, 1)
  }, {
    title: '12 months',
    since: new Date().addMonths(-12)
  }, {
    title: '6 months',
    since: new Date().addMonths(-6)
  }, {
    title: '3 months',
    since: new Date().addMonths(-3)
  }, {
    title: 'all'
  }];
  $scope.since = $scope.durations[0].since;
  $scope.setSince = function(since) {
    $scope.since = since;
  };
  $http.get('/api/daily').success(function(data){
    $scope.data = data.map(function(d){
      d.date = new Date(d.date);
      return d;
    });
  });
}])

.controller('ProjectCtrl', ['$scope', '$location', '$http', function($scope, $location, $http) {
  initPagination($scope);
  $scope.projectId = $location.path().split("/")[2];
  $scope.trend = {
    data: [],
    since: new Date(new Date().getFullYear()-1, 0, 1)
  };
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
        $scope.trend.data = commits
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
        $scope.trend.data = [];
        $scope.summary = {};
        $scope.users = [];
      }
    });
  });
}])

.controller('CommitCtrl', ['$scope', '$http', '$location', function($scope, $http, $location) {
  update();
  $scope.$watch(function () {
    return $location.path();
  }, function() {
    update();
  });

  function update() {
    $scope.projectId = $location.path().split("/")[2];
    $scope.commitId = $location.path().split("/")[3];

    $http.get('api/commit/' + $scope.projectId + '/' + $scope.commitId).success(function(data) {
      $scope.project = data['project'];
      $scope.commit = data['commit'];
      $scope.diffs = data['diffs'];
    });
  }

  $scope.url_for = function(diff) {
    return buildUrl('#/diff', {
      'projectId': $scope.project.id,
      'filename': diff.new.filename,
      'commitId': $scope.commit.sha1,
      'fileId': diff.new.sha1,
      'parentFileId': diff.old.sha1
    });
  };
}])

.controller('DiffCtrl', ['$scope', '$location', '$http',
    function($scope, $location, $http) {
  var search = $location.search();
  $scope.projectId = search.projectId;
  $scope.commitId = search.commitId;
  $scope.parentFileId = search.parentFileId;
  $scope.fileId = search.fileId;

  var url = 'api/diff/'
    + $scope.projectId + '/'
    + $scope.commitId + '/'
    + $scope.parentFileId + '/'
    + $scope.fileId;
  $http.get(url).success(function(data) {
    $scope.lines = data['lines'];
  });
}])

.controller('UsersCtrl', function($scope, $http) {
  initPagination($scope);
  $http.get('api/users').success(function(data) {
    $scope.users = data['users'];
  });
})

.controller('UserCtrl', ['$scope', '$http', '$location',
    function($scope, $http, $location) {
  $scope.userId = $location.path().split("/")[2];
  initPagination($scope);
  $http.get('api/user2?author=' + $scope.userId).success(function(data) {
    $scope.user = data['user'];
    $scope.commits = data['commits']
  });
}])

.filter('shorten', function() {
  return function(title) {
    // if title starts with [..] tags
    if (title)
      return title.replace(/^(\[.*\])(.*)/, '<small title="$1">[..]</small>$2');
    else
      return title;
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
