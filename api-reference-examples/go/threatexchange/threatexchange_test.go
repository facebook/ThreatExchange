// Copyright (c) Meta Platforms, Inc. and affiliates.
package threatexchange

import (
	"github.com/stretchr/testify/assert"
	"os"
	"testing"
)

var (
	appId     = os.Getenv("TX_APP_ID")     // Set this for integration tests
	appSecret = os.Getenv("TX_APP_SECRET") // Set this for integration tests
)

func TestQueryThreatDescriptorsOfIpsProxy(t *testing.T) {
	if len(appId) == 0 || len(appSecret) == 0 {
		t.SkipNow()
	}
	c, err := New(appId, appSecret, nil)
	if err != nil {
		t.Fatal(err)
	}
	res, rawJson, err := c.GetThreatIndicators("IP_ADDRESS", "proxy", "", "", 0, map[string]string{})
	if err != nil {
		t.Fatal(err)
	}
	assert.NotEmpty(t, res)
	assert.NotEmpty(t, rawJson)
	assert.NotEmpty(t, res.Data)

}

func TestQueryThreatDescriptorsOfIpsProxyByFBAdminOwner(t *testing.T) {
	if len(appId) == 0 || len(appSecret) == 0 {
		t.SkipNow()
	}
	c, err := New(appId, appSecret, nil)
	if err != nil {
		t.Fatal(err)
	}
	res, rawJson, err := c.GetThreatIndicators("IP_ADDRESS", "proxy", "", "", 0, map[string]string{"owner_app_id": "820763734618599"})
	if err != nil {
		t.Fatal(err)
	}
	assert.NotEmpty(t, res)
	assert.NotEmpty(t, rawJson)
	assert.NotEmpty(t, res.Data)
}

func TestQueryMalwareAnalysesInTimeRange(t *testing.T) {
	if len(appId) == 0 || len(appSecret) == 0 {
		t.SkipNow()
	}
	c, err := New(appId, appSecret, nil)
	if err != nil {
		t.Fatal(err)
	}
	res, rawJson, err := c.GetMalwareAnalyses("", "1391813489", "1391856689", 500, map[string]string{})
	if err != nil {
		t.Fatal(err)
	}
	assert.NotEmpty(t, res)
	assert.NotEmpty(t, rawJson)
	assert.NotEmpty(t, res.Data)

	assert.EqualValues(t, 266, len(res.Data))
}

func TestQueryMalwareFamiliesInTimeRange(t *testing.T) {
	if len(appId) == 0 || len(appSecret) == 0 {
		t.SkipNow()
	}
	c, err := New(appId, appSecret, nil)
	if err != nil {
		t.Fatal(err)
	}
	res, rawJson, err := c.GetMalwareFamilies("", "yesterday", "now", 500, map[string]string{})
	if err != nil {
		t.Fatal(err)
	}
	assert.NotEmpty(t, res)
	assert.NotEmpty(t, rawJson)
	assert.NotEmpty(t, res.Data)

}

func TestQueryGetAllMembers(t *testing.T) {
	if len(appId) == 0 || len(appSecret) == 0 {
		t.SkipNow()
	}
	c, err := New(appId, appSecret, nil)
	if err != nil {
		t.Fatal(err)
	}
	res, rawJson, err := c.GetThreatExchangeMembers()
	if err != nil {
		t.Fatal(err)
	}
	assert.NotEmpty(t, res)
	assert.NotEmpty(t, rawJson)
	assert.NotEmpty(t, res.Data)

}
