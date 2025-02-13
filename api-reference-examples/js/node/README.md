# node-threatexchange

This code is a node.js implementation of the Facebook Threat Exchange.

Documentation referenced in this project is located [here](https://github.com/facebook/ThreatExchange/blob/main/doc/threat_exchange.md)

## Usage

```
var threatexchange = require('node-threatexchange');

var app_id = 'APP_ID',
var app_secret ='APP_SECRET'

var api = threatexchange.createThreatExchange(app_id,app_secret);
```

Refer to `test/test.js` for usage of each endpoint.

Current endpoints implemented:

### /threat_exchange_members GET
GET request for list of threat_exchange_members

Usage:
```
api.getThreatExchangeMembers(function(err,data) {
    // process data from response here
});
```

### /malware_analyses GET
GET request for malware analyses

Usage:
```
var options = {}; // optional values as shown in Facebook documentation
api.getMalwareAnalyses(options,function(err,data) {
    // process data from response here
});
```

### /threat_indicators GET
GET request for threat indicators

Usage:
```
var options = {}; // optional values here as shown in Facebook documentation
api.getThreatIndicators(options,function(err,data) {
    // process data from response here
});
```

### /threat_indicators POST
POST request to add a threat indicator

Usage:
```
var options = {}; /* required options for adding a new threat indicator, helper function validatePostThreatIndicator is called and returns an error if necessary fields are missing */
api.postThreatIndicator(options,function(err,data) {
    // process response here
});
```

### /\<object_id\> (Malware) GET
GET request to retrieve information on an object ID pertaining to malware

Usage:
```
var fields = {}; // optional fields here as shown in Facebook documentation
var id = 12345; // unique ID to malware object
api.getMalwareObject(id,fields,function(err,data) {
    // process data here
});
```

### /\<object_id\> (Threat Indicator) GET
GET request to retrieve information on an object ID pertaining to a threat indicator

Usage:
```
var fields = {}; // optional fields here as shown in Facebook documentation
var id = 12345; // unique ID to threat indicator object
api.getThreatIndicatorObject(id,fields,function(err,data) {
    // process data here
});
```

### /\<object_id\> (Edit existing data) POST
POST request to edit an existing object

```
var options = {}; // fields to edit as shown in Facebook documentation
var id = 12345; // object to edit
api.editObject(id,options,function(err,data) {
    // process data here
});
```

### /\<object_id\>/related POST
POST request to add a connection to an \<object_id\>

```
var id1 = 12345; // original ID (the \<object_id\> in the url)
var id2 = 54321; // id to relate to id1
api.submitConnection(id1,id2,function(err,data) {
    // process data here 
});
```

### /\<object_id\>/related DEL
DEL request to remove a connection from \<object_id\>

```
var id1 = 12345; // original ID (the \<object_id\> in the url)
var id2 = 54321; // id to relate to id1
api.deleteConnection(id1,id2,function(err,data) {
    // process data here 
});
```

## Integration Tests

Run these to test integration with FBTE. Record once to cache everything
then run cache to play it back. Must use your APP_ID and APP_SECRET!


`VCR_MODE=record APP_ID='' APP_SECRET='' npm test`

`VCR_MODE=cache APP_ID='' APP_SECRET='' npm test`
