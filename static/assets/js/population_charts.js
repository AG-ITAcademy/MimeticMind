var echartAgeGroupsPieInit = function() {
  var $chartEl = document.querySelector('.echart-age-groups-pie');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        tooltip: {show:false},
        legend: {
          top: '5%',
          left: 'center',
          textStyle: {
            color: '#B2BEB5'
          }
        },
        series: [
          {
            name: 'Age Groups',
            type: 'pie',
            radius: ['40%', '70%'],  
            center: ['50%', '60%'],  
            avoidLabelOverlap: false,
            padAngle: 5,
            itemStyle: {
              borderRadius: 10
            },
            label: {
              show: true,
              position: 'outside',
              formatter: '{b}: {c} ({d}%)',
              color: '#B2BEB5',
              fontSize: 12,
              fontWeight: 'bold'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 16,
                fontWeight: 'bold',
                color: '#B2BEB5'
              }
            },
            labelLine: {
              show: true,
              length: 15,
              length2: 10,
              smooth: 0.2,
              lineStyle: {
                width: 1,
                type: 'solid',
                color: '#B2BEB5'
              }
            },
            data: [{name: 'Placeholder', value: 1}]
          }
        ]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.populationAgeGroupsChart = chart;
  }
};

var echartGenderDistributionInit = function() {
  var $chartEl = document.querySelector('.echart-gender-distribution');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        tooltip: {show:false},
        legend: {
          orient: 'horizontal',
          left: 'center',
          top: '5%',
          textStyle: {
            color: '#B2BEB5'
          }
        },
        series: [
          {
            name: 'Gender Distribution',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['50%', '55%'],  // Slightly lowered the center
            itemStyle: {
              borderRadius: 10
            },
            label: {
              show: true,
              position: 'outside',
              formatter: '{b}: {c} ({d}%)',
              color: '#B2BEB5',
              fontSize: 12,
              fontWeight: 'bold'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 16,
                fontWeight: 'bold',
                color: '#B2BEB5'
              }
            },
            labelLine: {
              show: true,
              length: 15,
              length2: 10,
              smooth: 0.2,
              lineStyle: {
                width: 1,
                type: 'solid',
                color: '#ffffff'
              }
            },
            data: [{name: 'Placeholder', value: 1}]
          }
        ]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.populationGenderDistributionChart = chart;
  }
};


var echartEducationIncomeInit = function() {
  var $chartEl = document.querySelector('.echart-education-income');
  if ($chartEl) {
    console.log("Initializing Education/Income chart");
    var chart = window.echarts.init($chartEl);
    var options = {
      tooltip: {
        position: 'top'
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        axisLabel: {
          color: '#B2BEB5'
        }
      },
      yAxis: {
        type: 'category',
        axisLabel: {
          color: '#B2BEB5'
        }
      },
      visualMap: {
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '5%'
      },
      series: [{
        type: 'heatmap',
        label: {
          show: true,
          color: '#000000'
        }
      }]
    };
    console.log("Setting initial chart options:", JSON.stringify(options, null, 2));
    chart.setOption(options);
    window.populationEducationIncomeChart = chart;
  } else {
    console.error("Education/Income chart element not found");
  }
};

var echartMaritalStatusInit = function() {
  var $chartEl = document.querySelector('.echart-marital-status');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        tooltip: {
          show: false
        },
        legend: {
          orient: 'horizontal',
          left: 'center',
          top: '5%',
          textStyle: {
            color: '#B2BEB5'
          }
        },
        series: [
          {
            name: 'Marital Status',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['50%', '55%'],
            padAngle: 5,
            itemStyle: {
              borderRadius: 10
            },
            label: {
              show: true,
              position: 'outside',
              formatter: '{b}: {c} ({d}%)',
              color: '#B2BEB5',
              fontSize: 12,
              fontWeight: 'bold'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 16,
                fontWeight: 'bold',
                color: '#B2BEB5'
              }
            },
            labelLine: {
              show: true,
              length: 15,
              length2: 10,
              smooth: 0.2,
              lineStyle: {
                width: 1,
                type: 'solid',
                color: '#B2BEB5'
              }
            },
            data: [
              { name: 'Single', value: 30 },
              { name: 'Married', value: 50 },
              { name: 'Divorced', value: 15 },
              { name: 'Widowed', value: 5 }
            ] // Placeholder data
          }
        ]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.populationMaritalStatusChart = chart;
  }
};

var echartHobbiesInit = function() {
  var $chartEl = document.querySelector('.echart-hobbies');
  if ($chartEl) {
    var userOptions = utils.getData($chartEl, 'options');
    var chart = window.echarts.init($chartEl);
    var getDefaultOptions = function() {
      return {
        tooltip: {
          trigger: 'item',
          formatter: function(params) {
            return params.name + ': ' + params.value.toFixed(2) + '%';
          }
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          textStyle: {
            color: '#B2BEB5'
          }
        },
        radar: {
          shape: 'circle',
          radius: '70%',  // Increased from default
          indicator: [
            { name: 'Sports', max: 100 },
            { name: 'Reading', max: 100 },
            { name: 'Music', max: 100 },
            { name: 'Travel', max: 100 },
            { name: 'Cooking', max: 100 },
            { name: 'Gaming', max: 100 }
          ],
          axisName: {
            color: '#B2BEB5'
          },
          splitArea: {
            areaStyle: {
              color: ['rgba(255, 255, 255, 0.05)', 'rgba(255, 255, 255, 0.1)']
            }
          },
          axisLine: {
            lineStyle: {
              color: 'rgba(255, 255, 255, 0.3)'
            }
          },
          splitLine: {
            lineStyle: {
              color: 'rgba(255, 255, 255, 0.2)'
            }
          }
        },
        series: [{
          name: 'Hobbies',
          type: 'radar',
          data: [
            {
              value: [80, 70, 60, 85, 50, 75],
              name: 'Interest Percentage'
            }
          ],
          symbol: 'circle',
          symbolSize: 8,
          itemStyle: {
            color: '#3498db'
          },
          areaStyle: {
            opacity: 0.3
          },
          lineStyle: {
            width: 2
          }
        }]
      };
    };
    echartSetOption(chart, userOptions, getDefaultOptions);
    window.populationHobbiesChart = chart;
  }
};



function updateEducationIncomeChart(data) {
  if (window.populationEducationIncomeChart && data.education_income) {
    var maxValue = Math.max(...data.education_income.map(item => item[2]));
    window.populationEducationIncomeChart.setOption({
      tooltip: {
        formatter: function (params) {
          var education = data.education_levels[params.data[0]];
          var income = data.income_levels[params.data[1]];
          var count = params.data[2];
          
          return 'Education: ' + education + '<br>' +
                 'Income: ' + income + '<br>' +
                 'Count: ' + count;
        }
      },
      xAxis: { 
        type: 'category',
        data: data.education_levels,
        axisLabel: {
          interval: 0,
          rotate: 30
        }
      },
      yAxis: { 
        type: 'category',
        data: data.income_levels
      },
      visualMap: {
        min: 0,
        max: maxValue,
        calculable: true
      },
      series: [{ 
        type: 'heatmap',
        data: data.education_income,
        label: {
          show: true
        }
      }]
    });
  }
}