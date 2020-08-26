# golang-threatexchange

A golang library to interface with Facebook ThreatExchange API. This is still very much in development so feel free to contribute :)

## Installation
`go get github.com/Facebook/ThreatExchange/api-reference-examples/go/threatexchange`

## Usage

The ThreatExchange library provides a base set of abstractions for the ThreatExchange API. You instantiate a new ThreatExchange Client and provide it with your appID and secret.

```golang

client, err = threatexchange.New(
	appID,
	appSecert,
	log.New(logrus.StandardLogger().Writer(), "ThreatExchange: ", log.Lshortfile),
)

```
To query the ThreatExchange API you use the client functions

```golang

ResultAsStruct, resultJson, err := client.GetMalwareAnalyses("TEXT_TO_SEARCH", "yesterday", "now", 500, map[string]string)
```

The result will return 3 objects,the first is an object that represent the result,
the second is the raw json of that result, and last is the error(nil if all went well).

##### Params for this func :

1. Text : to search by
2. StartTime : filter results by start time
3. EndTime : filter results by end time
4. Limit : results limits (if zero, will be ignored)
5. Additional params : to add to the query

Look into the test file for more examples of usage.
