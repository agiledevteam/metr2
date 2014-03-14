var metrServices = angular.module('metrServices', ['ngResource']);

metrServices.factory('ProjectList', ['$resource', function($resource){
	var resource =  $resource('/api/projects2', {}, {
  			query: {method:'GET', isArray:true}
  		});
	var query = resource.query();
	return {
		'projects' : query
	};
}]);