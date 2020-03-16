/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 * These are globals used by other JS files. Some are constants while others are
 * used to keep state or track content.
 */

// Your APP-ID
var app_id = "";
// Your APP-SECRET
var app_secret = "";
/**
 * The complete access token. If this is blank the UI will show a "thumbs-down".
 * The user can then enter their own app-id and app-secret through the UI and
 * this will get updated accordingly.
 */
var stored_token = window.localStorage.getItem("token");
if(stored_token !== null) {
    access_token = stored_token;
} else {
    var access_token = app_id + "|" + app_secret;
}

// URL constants.
var fbte_url = v_ThreatExchange.URL + v_ThreatExchange.VERSION;
var threat_descriptors = fbte_url + v_ThreatExchange.THREAT_DESCRIPTORS;
var threat_indicators = fbte_url + v_ThreatExchange.THREAT_INDICATORS;
var malware = fbte_url + v_ThreatExchange.MALWARE_ANALYSES;
var malware_families = fbte_url + v_ThreatExchange.MALWARE_FAMILIES;
var threat_exchange_members = fbte_url + v_ThreatExchange.THREAT_EXCHANGE_MEMBERS;

// Search counter used to generate unique div_ids for each search performed.
var search_counter = 0;

/**
 * Used to track which result was clicked on last. This allows us to remove the
 * active class when another is clicked on without having to do a search through
 * the DOM to find it.
 */
var highlighted_result = null;
