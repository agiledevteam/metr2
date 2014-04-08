module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    uglify: {
      options: {
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("yyyy-mm-dd") %> */\n'
      },
      build: {
        src: 'src/<%= pkg.name %>.js',
        dest: 'build/<%= pkg.name %>.min.js'
      }
    },
    bower: {
      dev: {
        dest: 'metrapp/static',
        js_dest: 'metrapp/static/js',
        css_dest: 'metrapp/static/css',
        options: {
          packageSpecific: {
            bootstrap: {
              files: [
                "./dist/js/bootstrap.js",
                "./dist/css/bootstrap.css",
                "./dist/fonts/glyphicons-halflings-regular.eot",
                "./dist/fonts/glyphicons-halflings-regular.svg",
                "./dist/fonts/glyphicons-halflings-regular.ttf",
                "./dist/fonts/glyphicons-halflings-regular.woff"
              ],
              dest: 'metrapp/static/fonts',
              js_dest: 'metrapp/static/js',
              css_dest: 'metrapp/static/css'
            }
          }
        }
      }
    }
  });

  // Load the plugin that provides the "uglify" task.
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-bower');

  // Default task(s).
  grunt.registerTask('default', ['uglify']);

};