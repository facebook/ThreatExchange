// Copyright (c) Meta Platforms, Inc. and affiliates.
var ThreatExchange = require('./lib/threatexchange');
exports.createThreatExchange = function createThreatExchange(app_id,app_secret) {
  return ThreatExchange(app_id,app_secret);
}
