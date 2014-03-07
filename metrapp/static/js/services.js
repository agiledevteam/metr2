var metrServices = angular.module('metrServices', ['ngResource']);
 
metrServices.factory('Metr', ['$resource',
  function($resource){
    return $resource('api/projects', {}, {
      projects: {method:'GET', isArray:true}
    });
  }]);