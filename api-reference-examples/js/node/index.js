// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
var ThreatExchange = require('./lib/threatexchange');
exports.createThreatExchange = function createThreatExchange(app_id,app_secret) {
  return ThreatExchange(app_id,app_secret);
}
