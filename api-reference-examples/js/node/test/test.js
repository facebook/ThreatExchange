// Copyright (c) Meta Platforms, Inc. and affiliates.
var mocha = require('mocha');
var assert = require('assert');
var should = require('chai').should;
var expect = require('chai').expect;
var threatexchange = require('../index');
var sepia = require('sepia');
var app_id = process.env.APP_ID;
var app_secret = process.env.APP_SECRET;

describe('Threatexchange object unit tests', function() {
  it('should error out if app credentials are missing', function(done) {
    expect(function() {
      threatexchange.createThreatExchange(null,null)
    })
    .to
    .throw('set app_id / app_secret!');
    done();
  });
});

describe('/threat_exchange_members GET', function() {
  it('should return a list of members given correct app credentials', function(done) {
    var api = threatexchange.createThreatExchange(app_id,app_secret);
    api.getThreatExchangeMembers(function (err, data) {
      if(err) {
        done(err);
      } else {
        expect(data.data.length).to.not.be.empty;
        done();
      }
    });
  }); 
});

describe('/threatindicators POST', function() {
  it('should error out if the required fields are not present', function(done) {
    var api = threatexchange.createThreatExchange(app_id,app_secret);
    expect(function() {
      api.postThreatIndicators({'bad_data':'bad'}, function(err,data){
        if(err) throw(err)
      })
    })
    .to
    .throw(Error);
    done();
  });
  it('should successfully create a new threat indicator from the examples', function(done) {
    var api = threatexchange.createThreatExchange(app_id,app_secret);
    var options = {};
    options['indicator'] = 'evil-domain.biz'
    options['type'] = api.vocabulary.v_Types.DOMAIN; 
    options['threat_type'] = api.vocabulary.v_ThreatType.MALICIOUS_DOMAIN;
    options['status'] = api.vocabulary.v_Status.MALICIOUS; 
    options['description'] = 'This domain was hosting malware';
    options['privacy_type'] = api.vocabulary.v_PrivacyType.VISIBLE;
    api.postThreatIndicators(options, function(err,data) {
      if(err) {
        done(err);
      } else {
        expect(data['id']).to.equal('810975008991121'); 
        done();
      }
    }); 
  });
});

describe('/threat_indicators GET', function() {
  it('should return malicious IP addresses that are proxies', function(done) {
    var api = threatexchange.createThreatExchange(app_id,app_secret);
    var options = {};
    options['type'] = api.vocabulary.v_Types.IP_ADDRESS; 
    options['text'] = 'proxy';
    api.getThreatIndicators(options, function(err,data) {
      if(err) {
        done(err);
      } else {
        expect(data.data.length).to.not.be.empty;
        done(); 
      }
    });
  });
});

describe('/malware_analyses GET', function() {
  it('should return results for a text query of \'malware\'', function(done) {
    var api = threatexchange.createThreatExchange(app_id,app_secret);
    api.getMalwareAnalyses({'text' : 'malware'}, function(err, data) {
      if(err) {
        done(err)
      } else {
        expect(data.data.length).to.not.be.empty;
        done();
      }
    });
  })
});

describe('/malwareobject GET', function() {
  it('should return md5 results for a malware object query on 518964484802467', function(done) {
    var api = threatexchange.createThreatExchange(app_id,app_secret);
    var malId = '518964484802467';
    api.getMalwareObject(malId,['md5'], function(err, data) {
      if(err) {
        done(err);
      } else {
        expect(data['md5']).to.equal('31a345a897ef34cf2a5ce707d217ac6b');
        done();
      }
    });
  });
});

describe('/malwarefamilyobject GET', function() {
  it('should return added_on,id,name & status for malware sample 812860802080929', function(done) {
    var api = threatexchange.createThreatExchange(app_id,app_secret);
    var malId = '812860802080929';
    api.getMalwareFamilyObjects(malId,['added_on','id','name','description'], function(err, data) {
      if(err) {
        done(err);
      } else {
        expect(data).to.contain.all.keys(['added_on','id','name','description']);
        done();
      }
    });
  })
});

describe('/threatindicatorobject GET', function() {
  it('should return \'facebook.com\' in indicator field for threat indicator '
      + 'object id 788497497903212', function(done) {
    var api = threatexchange.createThreatExchange(app_id,app_secret);
    var threatIndId = '788497497903212';
    api.getThreatIndicatorObject(threatIndId,['indicator'], function(err, data) {
      if(err) {
        done(err);
      } else {
        expect(data['indicator']).to.equal('facebook.com');
        done();
      }
    });
  })
});

describe('/objectid POST edit', function() {
  it('should sucessfully change the description field of object' 
    + 'id 788497497903212', function(done) {
    var api = threatexchange.createThreatExchange(app_id,app_secret);
    var threatIndId = '788497497903212';
    api.editObject(threatIndId,{'description':'Facebook'}, function(err,data) {
      if(err) {
        done(err);
      } else {
        expect(data['success']).to.equal(true);
        done();
      }
    });
  });
});

describe('/objectid/related POST create', function() {
  it(' should successfully create a related link between 788497497903212 and'
    + '1061383593887032', function(done) {
    var api = threatexchange.createThreatExchange(app_id,app_secret);
    var id1 = '788497497903212';
    var id2 = '1061383593887032';
    api.submitConnection(id1,id2, function(err,data) {
      if(err) {
        done(err);
      } else {
        expect(data['success']).to.equal(true);
        done();
      } 
    });
  }); 
});

describe('/objectid/related DEL', function() {
  it('should successfully delete a related link between 788497497903212 and'
    + ' 1061383593887032', function(done) {
    var api = threatexchange.createThreatExchange(app_id,app_secret);
    var id1 = '788497497903212';
    var id2 = '1061383593887032';
    api.deleteConnection(id1,id2, function(err,data) {
      if(err) {
        done(err);
      } else {
        expect(data['success']).to.equal(true);
        done();
      } 
    });
  }); 
});
