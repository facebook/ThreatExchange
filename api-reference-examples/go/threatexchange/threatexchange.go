// Copyright (c) Meta Platforms, Inc. and affiliates.
package threatexchange

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
)

const (
	// DefaultURL is the URL for the API endpoint
	DefaultURL = "https://graph.facebook.com"
	apiVersion = "v2.5"
)

// Client interacts with the services provided by TE
type Client struct {
	appId     string
	appSecret string
	logger    *log.Logger
	c         *http.Client
}

type MalwareFamiliesResults struct {
	Data   []MalwareFamilyResult `json:"data"`
	Paging ResultPaging          `json:"paging,omitempty"`
	Next   string                `json:"next,omitempty"`
}

type MalwareFamilyResult struct {
	ID             string   `json:"id"`
	Aliases        []string `json:"aliases,omitempty"`
	AddedOn        string   `json:"added_on,omitempty"`
	Description    string   `json:"description,omitempty"`
	FamilyType     string   `json:"family_type,omitempty"`
	Malicious      string   `json:"malicious,omitempty"`
	Name           string   `json:"name,omitempty"`
	SampleCount    int      `json:"sample_count,omitempty"`
	SubmitterCount int      `json:"submitter_count,omitempty"`
}
type MalwareResults struct {
	Data   []MalwareResult `json:"data"`
	Paging ResultPaging    `json:"paging,omitempty"`
	Next   string          `json:"next,omitempty"`
}

type MalwareResult struct {
	ID             string `json:"id"`
	Crx            string `json:"crx,omitempty"`
	PEHash         string `json:"imphash,omitempty"`
	MD5            string `json:"md5,omitempty"`
	Password       string `json:"password,omitempty"`
	PEHeader       string `json:"pe_rich_header,omitempty"`
	Sample         string `json:"sample,omitempty"`
	SampleType     string `json:"sample_type,omitempty"`
	Sha1           string `json:"sha1,omitempty"`
	Sha256         string `json:"sha256,omitempty"`
	ShareLevel     string `json:"share_level,omitempty"`
	Ssdeep         string `json:"ssdeep,omitempty"`
	SubmitterCount string `json:"submitter_count,omitempty"`
	VictimCount    int    `json:"victim_count,omitempty"`
	Xpi            string `json:"xpi,omitempty"`
	Status         string `json:"status,omitempty"`
	AddedOn        string `json:"added_on,omitempty"`
	PrivacyType    string `json:"privacy_type,omitempty"`
}

type ThreatDescriptorResults struct {
	Data   []ThreatDescriptor `json:"data"`
	Paging ResultPaging       `json:"paging,omitempty"`
	Next   string             `json:"next,omitempty"`
}

type ResultPaging struct {
	Cursors Cursors `json:"cursors"`
}

type Cursors struct {
	Before string `json:"before,omitempty"`
	After  string `json:"after,omitempty"`
}

type ThreatDescriptor struct {
	ID           string          `json:"id"`
	Indicator    IndicatorResult `json:"indicator,omitempty"`
	Owner        TEOwner         `json:"owner,omitempty"`
	Type         string          `json:"type,omitempty"`
	RawIndicator string          `json:"raw_indicator,omitempty"`
	Description  string          `json:"description,omitempty"`
	Status       string          `json:"status,omitempty"`
	PrivacyType  string          `json:"privacy_type,omitempty"`
	ShareLevel   string          `json:"share_level,omitempty"`
	AddedOn      string          `json:"added_on,omitempty"`
	Confidence   int             `json:"confidence,omitempty"`
	ExpiredOn    string          `json:"expired_on,omitempty"`
	LastUpdated  string          `json:"last_updated,omitempty"`
	SourceUri    string          `json:"source_uri,omitempty"`
}

type IndicatorResult struct {
	ID        string `json:"id,omitempty"`
	Indicator string `json:"indicator,omitempty"`
	Type      string `json:"type,omitempty"`
}

type TEOwner struct {
	ID    string `json:"id,omitempty"`
	Email string `json:"email,omitempty"`
	Name  string `json:"name,omitempty"`
}

type TEOwnersResults struct {
	Data   []TEOwner    `json:"data"`
	Paging ResultPaging `json:"paging,omitempty"`
	Next   string       `json:"next,omitempty"`
}

// New - will create a new ThreatExchange Go client, log param may be nil.
func New(appID, appSecret string, log *log.Logger) (*Client, error) {
	c := &Client{
		appId:     appID,
		appSecret: appSecret,
		logger:    log,
		c:         http.DefaultClient,
	}
	return c, nil
}

// errorf logs to the error log.
func (c *Client) errorf(format string, args ...interface{}) {
	if c.logger != nil {
		c.logger.Printf(format, args...)
	}
}

// GetThreatIndicators - is a query to retrieve ThreatIndicators, will return ThreatDescriptorResults to hold results, and raw json of that
// limit of size <=0 will be ignored
func (c *Client) GetThreatIndicators(resourceType, text, startTime, endTime string, limit int,
	extraParams map[string]string) (*ThreatDescriptorResults, string, error) {
	var result = &ThreatDescriptorResults{}
	res, err := c.query(apiVersion, "threat_descriptors", startTime, endTime, resourceType, text, limit, extraParams, result)
	if err != nil {
		return nil, "", err
	}

	return result, res, nil
}

// GetMalwareAnalyses - is a query to retrieve Malware Analyses, will return MalwareResults to hold results, and raw json of that
func (c *Client) GetMalwareAnalyses(text, startTime, endTime string, limit int,
	extraParams map[string]string) (*MalwareResults, string, error) {
	var result = &MalwareResults{}
	res, err := c.query(apiVersion, "malware_analyses", startTime, endTime, "", text, limit, extraParams, result)
	if err != nil {
		return nil, "", err
	}
	return result, res, nil
}

// GetMalwareFamilies - is a query to retrieve ThreatIndicators, will return MalwareFamiliesResults to hold results, and raw json of that
func (c *Client) GetMalwareFamilies(text, startTime, endTime string, limit int,
	extraParams map[string]string) (*MalwareFamiliesResults, string, error) {
	var result = &MalwareFamiliesResults{}
	res, err := c.query(apiVersion, "malware_families", startTime, endTime, "", text, limit, extraParams, result)
	if err != nil {
		return nil, "", err
	}
	return result, res, nil
}

// GetThreatExchangeMembers - is a query to retrieve ThreatExchange members, will return TEOwnersResults to hold results, and raw json of that
func (c *Client) GetThreatExchangeMembers() (*TEOwnersResults, string, error) {
	var result = &TEOwnersResults{}
	res, err := c.query(apiVersion, "threat_exchange_members", "", "", "", "", 0, map[string]string{}, result)
	if err != nil {
		return nil, "", err
	}

	return result, res, nil
}

func (c *Client) query(apiVersion string, resource string, startTime string, endTime string, resourceType string,
	text string, limit int, extraParams map[string]string, result interface{}) (string, error) {
	u, err := url.Parse(DefaultURL)
	if err != nil {
		c.errorf("Could not parse url %s", u.String())
		return "", err
	}

	parameters := url.Values{}
	parameters.Add("access_token", fmt.Sprintf("%s|%s", c.appId, c.appSecret))
	if len(startTime) > 0 {
		parameters.Add("since", startTime)
	}
	if len(endTime) > 0 {
		parameters.Add("until", endTime)
	}
	if len(resourceType) > 0 {
		parameters.Add("type", resourceType)
	}
	if len(text) > 0 {
		parameters.Add("text", text)
	}
	if limit > 0 {
		parameters.Add("limit", fmt.Sprintf("%d", limit))
	}
	for k, v := range extraParams {
		parameters.Add(k, v)
	}
	u.RawQuery = parameters.Encode()
	u.Path += fmt.Sprintf("/%s/%s/", apiVersion, resource)

	res, err := http.Get(u.String())
	if err != nil {
		return "", err
	}
	if res.Body == nil {
		return "", fmt.Errorf("Empty body for query : %s", u.String())
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		c.errorf("Wrong http return code, got : %d", res.StatusCode)
		return "", fmt.Errorf("Wrong http return code, got : %d", res.StatusCode)
	}
	byteRes, err := ioutil.ReadAll(res.Body)
	if err != nil {
		c.errorf("Could not read response body : %v", err)
		return "", err
	}
	err = json.Unmarshal(byteRes, result)
	if err != nil {
		c.errorf("Could not Unmarshal response body : %s, for resource : %s", string(byteRes), resource)
		return "", err
	}
	return string(byteRes), nil
}
