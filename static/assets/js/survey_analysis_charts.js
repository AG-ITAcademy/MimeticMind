// survey_analysis_charts.js

// Box Plot Chart Initialization
var echartBoxPlotInit = function() {
  var $chartEl = document.querySelector('.echart-box-plot');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        tooltip: {
          trigger: 'item',
          axisPointer: { type: 'shadow' }
        },
        grid: {
          left: '10%',
          right: '10%',
          bottom: '15%'
        },
        xAxis: {
          type: 'category',
          data: ['Placeholder'],
          boundaryGap: true,
          nameGap: 30,
          splitArea: { show: false },
          axisLabel: { show: true },
          splitLine: { show: false }
        },
        yAxis: {
          type: 'value',
          splitArea: { show: true }
        },
        series: [{
          name: 'boxplot',
          type: 'boxplot',
          data: [[850, 900, 950, 1000, 1050]]
        }]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.surveyBoxPlotChart = chart;
  }
};

// Histogram Chart Initialization
var echartHistogramInit = function() {
  var $chartEl = document.querySelector('.echart-histogram');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' }
        },
        grid: {
          left: '10%',
          right: '10%',
          bottom: '15%'
        },
        xAxis: {
          type: 'category',
          data: ['Placeholder'],
          boundaryGap: true
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          type: 'bar',
          data: [1],
          barWidth: '99%'
        }]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.surveyHistogramChart = chart;
  }
};

// Pie Chart Initialization
var echartPieChartInit = function() {
  var $chartEl = document.querySelector('.echart-pie-chart');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 10,
          data: ['Placeholder']
        },
        series: [{
          name: 'Data',
          type: 'pie',
          radius: '50%',
          data: [{ value: 1, name: 'Placeholder' }]
        }]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.surveyPieChart = chart;
  }
};

// Word Cloud Chart Initialization
var echartWordCloudInit = function() {
  var $chartEl = document.querySelector('.echart-word-cloud');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        series: [{
          type: 'wordCloud',
          shape: 'circle',
          left: 'center',
          top: 'center',
          width: '70%',
          height: '80%',
          right: null,
          bottom: null,
          sizeRange: [12, 60],
          rotationRange: [-90, 90],
          rotationStep: 45,
          gridSize: 8,
          drawOutOfBound: false,
          textStyle: {
            normal: {
              fontFamily: 'sans-serif',
              fontWeight: 'bold',
              color: function () {
                return 'rgb(' + [
                  Math.round(Math.random() * 160),
                  Math.round(Math.random() * 160),
                  Math.round(Math.random() * 160)
                ].join(',') + ')';
              }
            },
            emphasis: {
              shadowBlur: 10,
              shadowColor: '#333'
            }
          },
          data: [{ name: 'Placeholder', value: 1 }]
        }]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.surveyWordCloudChart = chart;
  }
};

// Bar Chart Initialization
var echartBarChartInit = function() {
  var $chartEl = document.querySelector('.echart-bar-chart');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' }
        },
        grid: {
          left: '10%',
          right: '10%',
          bottom: '15%'
        },
        xAxis: {
          type: 'category',
          data: ['Placeholder']
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          type: 'bar',
          data: [1]
        }]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.surveyBarChart = chart;
  }
};

// Scatter Plot Initialization
var echartScatterPlotInit = function() {
  var $chartEl = document.querySelector('.echart-scatter-plot');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        tooltip: {
          trigger: 'item',
          axisPointer: { type: 'cross' }
        },
        xAxis: {
          type: 'value',
          splitLine: { lineStyle: { type: 'dashed' } }
        },
        yAxis: {
          type: 'value',
          splitLine: { lineStyle: { type: 'dashed' } }
        },
        series: [{
          type: 'scatter',
          data: [[0, 0]]
        }]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.surveyScatterPlotChart = chart;
  }
};

// Horizontal Bar Chart Initialization
var echartHorizontalBarChartInit = function() {
  var $chartEl = document.querySelector('.echart-horizontal-bar-chart');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' }
        },
        grid: {
          left: '10%',
          right: '10%',
          bottom: '15%'
        },
        xAxis: {
          type: 'value'
        },
        yAxis: {
          type: 'category',
          data: ['Placeholder']
        },
        series: [{
          type: 'bar',
          data: [1]
        }]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.surveyHorizontalBarChart = chart;
  }
};

// Stacked Bar Chart Initialization
var echartStackedBarChartInit = function() {
  var $chartEl = document.querySelector('.echart-stacked-bar-chart');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' }
        },
        legend: {
          data: ['Placeholder1', 'Placeholder2']
        },
        grid: {
          left: '10%',
          right: '10%',
          bottom: '15%'
        },
        xAxis: {
          type: 'category',
          data: ['Placeholder']
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: 'Placeholder1',
            type: 'bar',
            data: [1]
          },
          {
            name: 'Placeholder2',
            type: 'bar',
            data: [2]
          }
        ]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.surveyStackedBarChart = chart;
  }
};


//update scripts


        function updateSurveyAnalysisCharts(chartData, schema) {
            console.log('Updating charts with data:', chartData, 'Schema:', schema);

            switch(schema) {
                case 'ScaleSchema':
                    updateHistogramChart(chartData);
                    break;
                case 'OpenEndedSchema':
                    updateWordCloudChart(chartData);
                    break;
                case 'MultipleChoiceSchema':
                case 'YesNoSchema':
                    updatePieChart(chartData);
                    break;
                case 'RankingSchema':
                    updateBarChart(chartData);
                    break;
                default:
                    console.error('Unknown schema type:', schema);
            }
        }

        function updateHistogramChart(data) {
            if (charts.histogram) {
                const items = data.map(item => item.item);
                const values = data.map(item => parseInt(item.response));
                charts.histogram.setOption({
                    xAxis: { 
                        type: 'category',
                        data: items
                    },
                    yAxis: { type: 'value' },
                    series: [{ 
                        data: values,
                        type: 'bar'
                    }]
                });
            }
        }

        function updateWordCloudChart(data) {
            if (charts.wordCloud) {
                const wordFrequency = data.map(item => ({
                    name: item.item,
                    value: parseInt(item.response)
                }));
                charts.wordCloud.setOption({
                    series: [{ 
                        type: 'wordCloud',
                        data: wordFrequency,
                        sizeRange: [12, 50],
                        rotationRange: [-90, 90],
                        shape: 'circle',
                        textStyle: {
                            normal: {
                                color: function () {
                                    return 'rgb(' + [
                                        Math.round(Math.random() * 160),
                                        Math.round(Math.random() * 160),
                                        Math.round(Math.random() * 160)
                                    ].join(',') + ')';
                                }
                            },
                            emphasis: {
                                shadowBlur: 10,
                                shadowColor: '#333'
                            }
                        }
                    }]
                });
            }
        }

        function updatePieChart(data) {
            if (charts.pieChart) {
                const pieData = data.map(item => ({
                    name: item.item,
                    value: parseInt(item.response)
                }));
                charts.pieChart.setOption({
                    tooltip: {
                        trigger: 'item',
                        formatter: '{a} <br/>{b}: {c} ({d}%)'
                    },
                    series: [{ 
                        name: 'Distribution',
                        type: 'pie',
                        radius: '50%',
                        data: pieData
                    }]
                });
            }
        }

        function updateBarChart(data) {
            if (charts.barChart) {
                const items = data.map(item => item.item);
                const values = data.map(item => parseInt(item.response));
                charts.barChart.setOption({
                    xAxis: { 
                        type: 'category',
                        data: items
                    },
                    yAxis: { type: 'value' },
                    series: [{ 
                        data: values,
                        type: 'bar'
                    }]
                });
            }
        }