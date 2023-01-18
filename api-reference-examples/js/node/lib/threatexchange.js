// Copyright (c) Meta Platforms, Inc. and affiliates.
var request = require('request');
var vocabulary = require('./vocabulary');

var ThreatExchange = function(app_id, app_secret) {

  if (app_id == undefined ||
      app_secret == undefined) {
    throw new Error('set app_id / app_secret!');
  }

  var fbte_url = vocabulary.v_ThreatExchange.URL + 
    vocabulary.v_ThreatExchange.VERSION;
  var threat_indicators = fbte_url + 
    vocabulary.v_ThreatExchange.THREAT_INDICATORS;
  var malware = fbte_url + vocabulary.v_ThreatExchange.MALWARE_ANALYSES;
  var threat_exchange_members = fbte_url + 
    vocabulary.v_ThreatExchange.THREAT_EXCHANGE_MEMBERS;

  var exportObj = {
    app_id : app_id,
    app_secret : app_secret,
    access_token : app_id + '|' + app_secret,
    vocabulary : vocabulary,
  };

  exportObj.getThreatExchangeMembers = function(callback) {
    options= { access_token : exportObj.access_token }
    request({url:threat_exchange_members,qs:options},function (err,response,body) {
        if (err) {
          callback(err,null);
        } else {
          if (response.statusCode != 200) {
            callback(new Error({statusCode:response.statusCode,body:response.body}),null);
          } else {
            callback(null,JSON.parse(body));
          }
        }
    });
  };

  exportObj.postThreatIndicators = function(options,callback) {
    options['access_token'] = exportObj.access_token;
    exportObj.validatePostThreatIndicator(options, function(err) {
      if (err) callback(err);
      request.post({url:threat_indicators,form:options}, function (err,response,body) {
        if (err) { 
          callback(err,null);
        } else {
          if (response.statusCode != 200) {
            callback(new Error(JSON.stringify({statusCode:response.statusCode,body:response.body})),null);
          } else {
            callback(null,JSON.parse(response.body));
          } 
        }
      }); 
    });
  };

  exportObj.validatePostThreatIndicator = function(options,callback) {
    var required = ['description','indicator','privacy_type','status','type']
    required.forEach(function(field) {
      if(!(field in options)) { 
        callback(new Error('fields missing in options, expected:' 
          + required +'\nreceived:'+JSON.stringify(options)));
      }
    });
    callback(null);
  };

  exportObj.getMalwareAnalyses = function (options,callback) {
    options['access_token'] = exportObj.access_token;
    request({url:malware,qs:options},function (err,response,body) {
        if (err) {
          callback(err,null)
        } else {
          if (response.statusCode != 200) {
            callback(new Error(JSON.stringify({statusCode:response.statusCode,body:response.body})), null);
          } else {
            callback(null,JSON.parse(body));
          }
        }
      });
  };

  exportObj.getMalwareObject = function (id,fields,callback) {
    options['access_token'] = exportObj.access_token;
    if(isNaN(id)) {
      callback(new Error(id + ' is not a number!'),null);
    } else {
      if(fields.length > 0) {
        options['fields'] = fields.join();
        request({url:fbte_url+id,qs:options},function (err,response,body) {
          if(err) {
            callback(err,null);
          } else {
            if (response.statusCode != 200) {
              callback(new Error(JSON.stringify({statusCode:response.statusCode,body:response.body})),null);
            } else {
              callback(null,JSON.parse(body));
            }
          } 
        });
      } else {
        callback(new Error('fields is empty'),null);
      } 
    }
  };

  exportObj.getMalwareFamilyObjects = function (id,fields,callback) {
    options['access_token'] = exportObj.access_token;
    if(isNaN(id)) {
      callback(new Error(id + ' is not a number!'),null);
    } else {
      if(fields.length > 0) {
        options['fields'] = fields.join();
        request({url:fbte_url+id,qs:options},function (err,response,body) {
          if(err) {
            callback(err,null);
          } else {
            if (response.statusCode != 200) {
              callback(new Error(JSON.stringify({statusCode:response.statusCode,body:response.body})),null);
            } else {
              callback(null,JSON.parse(body));
            }
          } 
        });
      } else {
        callback(new Error('fields is empty'),null);
      } 
    }
  };

  exportObj.getThreatIndicatorObject = function (id,fields,callback) {
    options['access_token'] = exportObj.access_token;
    if(isNaN(id)) {
      callback(new Error(id + ' is not a number!',null));
    } else {
      if(fields.length > 0) {
        options['fields'] = fields.join();
        request({url:fbte_url+id,qs:options},function(err,response,body) {
            if(err) {
              callback(err,null);
            } else {
              if (response.statusCode != 200) {
                callback(new Error(JSON.stringify({statusCode:response.statusCode,body:response.body})),null);
              } else {
                callback(null,JSON.parse(body));
              }
            }
        });
      } else {
        callback(new Error('fields is empty'),null);
      }
    }
  };

  exportObj.editObject = function (id,options,callback) {
    options['access_token'] = exportObj.access_token;
    if(isNaN(id)) {
      callback(new Error(id + ' is not a number!',null));
    } else {
      request.post({url:fbte_url+id,form:options}, function (err,response,body) {
        if (err) { 
          callback(err,null);
        } else {
          if (response.statusCode != 200) {
            callback(new Error(JSON.stringify({statusCode:response.statusCode,body:response.body})),null);
          } else {
            callback(null,JSON.parse(response.body));
          } 
        }
      }); 
    }
  };
  
  exportObj.submitConnection = function (id1,id2,callback) {
    options['access_token'] = exportObj.access_token;
    var url = fbte_url + id1 + '/related';
    if(isNaN(id1) || isNaN(id2)) {
      callback(new Error(id1 + ',' + id2 + ' not numbers!'));
    } else {
      options['related_id'] = id2;
      request.post({url:url,form:options}, function (err,response,body) {
        if(err) {
          callback(err,null);
        } else {
          if (response.statusCode != 200) {
            callback(new Error(JSON.stringify({statusCode:response.statusCode,body:response.body})),null);
          } else {
            callback(null,JSON.parse(response.body));
          }
        }
      });
    }
  };    

  exportObj.deleteConnection = function (id1,id2,callback) {
    options['access_token'] = exportObj.access_token;
    var url = fbte_url + id1 + '/related';
    if(isNaN(id1) || isNaN(id2)) {
      callback(new Error(id1 + ',' + id2 + ' not numbers!'));
    } else {
      options['related_id'] = id2;
      request.del({url:url,qs:options}, function (err,response,body) {
        if(err) {
          callback(err,null);
        } else {
          if(response.statusCode != 200) {
            callback(new Error(JSON.stringify({statusCode:response.statusCode,body:response.body})),null);
          } else {
            callback(null,JSON.parse(response.body));
          }
        }
      });
    }
  };

  exportObj.getThreatIndicators = function (options,callback) {
    options['access_token'] = exportObj.access_token;
    request({url:threat_indicators,qs:options}, function (err,response, body) {
      if(err) {
        callback(err,null); 
      } else {
        if(response.statusCode != 200) {
          callback(new Error(JSON.stringify({statusCode:response.statusCode,body:response.body})),null);
        } else {
          callback(null,JSON.parse(response.body));
        } 
      }
    });
  };

  return exportObj;
  
}

module.exports = ThreatExchange;
