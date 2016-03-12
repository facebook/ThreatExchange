# golang-threatexchange

A golang library to interface with Facebook ThreatExchange API. This is still very much in development so feel free to contribute :)

## Installation
``` go get github.com/meirwah/ThreatExchange/golang/threatexchange```

## Usage

The ThreatExchange library provides a base set of abstractions for the ThreatExchange API. You instantiate a new ThreatExchange Client and provide it with your appID and secret.

```golang

client, err = threatexchange.New(
	appID,
	appSecert,
	log.New(conf.LogWriter, "ThreatExchange: ", log.Lshortfile),
)

```
To query the ThreatExchange API you use the client functions

```golang

ResultAsStruct, resultJson, err := client.GetMalwareAnalyses("TEXT_TO_SEARCH", "yesterday", "now", 500, map[string]string)
```

The result will return 3 objects,the firs tis an object that represent the result,
the second is the raw json of that result, and last is the error(nil if all went well).

Params for this func:
1. "text" : to search by
2. "startTime" : filter results by start time.
3. "endTime" : filter results by end time.
4. "limit" : results limits (if zero, will be ignored)
5. "Additional params" : to add to the query.

Look into the test file for more examples of usage.


## Contributing

1. Fork it
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create a new Pull Request
