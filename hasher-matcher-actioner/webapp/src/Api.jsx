/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import {Auth, API} from 'aws-amplify';

async function getAuthorizationToken() {
  const currentSession = await Auth.currentSession();
  const accessToken = currentSession.getAccessToken();
  const jwtToken = accessToken.getJwtToken();
  return jwtToken;
}

async function apiGet(route, params = {}, responseType = null) {
  return API.get('hma_api', route, {
    responseType,
    headers: {
      Authorization: await getAuthorizationToken(),
    },
    queryStringParameters: params,
  });
}

async function apiPost(route, body, params = {}) {
  return API.post('hma_api', route, {
    body,
    headers: {
      Authorization: await getAuthorizationToken(),
    },
    queryStringParameters: params,
  });
}

async function apiPut(route, body, params = {}) {
  return API.put('hma_api', route, {
    body,
    headers: {
      Authorization: await getAuthorizationToken(),
    },
    queryStringParameters: params,
  });
}

async function apiDelete(route, params = {}) {
  return API.del('hma_api', route, {
    headers: {
      Authorization: await getAuthorizationToken(),
    },
    queryStringParameters: params,
  });
}

export function fetchAllMatches() {
  return apiGet('/matches/');
}

export function fetchMatchesFromSignal(signalSource, signalId) {
  return apiGet('/matches/', {
    signal_q: signalId,
    signal_source: signalSource,
  });
}

export function fetchMatchesFromContent(contentId) {
  return apiGet('/matches/', {content_q: contentId});
}

export function fetchMatchDetails(contentId) {
  return apiGet('/matches/match/', {content_id: contentId});
}

export function fetchHash(contentId) {
  return apiGet('/content/hash/', {content_id: contentId});
}

export function fetchImage(contentId) {
  return apiGet('/content/image/', {content_id: contentId});
}

export function fetchContentActionHistory(contentId) {
  return apiGet('/content/action-history/', {content_id: contentId});
}

export function fetchContentDetails(contentId) {
  return apiGet('/content/', {
    content_id: contentId,
  });
}

export function fetchContentPipelineProgress(contentId) {
  return apiGet('/content/pipeline-progress/', {
    content_id: contentId,
  });
}

export function fetchSignalSummary() {
  return apiGet('/signals');
}

export function fetchDashboardCardSummary(path) {
  return apiGet(`/${path}`);
}

export function fetchStats(statName, timeSpan) {
  return apiGet('/stats/', {stat_name: statName, time_span: timeSpan});
}

export async function requestSignalOpinionChange(
  signalId,
  signalSource,
  dataset,
  opinionChange,
) {
  apiPost(
    '/matches/request-signal-opinion-change/',
    {},
    {
      signal_q: signalId,
      signal_source: signalSource,
      dataset_q: dataset,
      opinion_change: opinionChange,
    },
  );
}

export async function submitContentViaURL(
  contentId,
  contentType,
  additionalFields,
  content,
) {
  return apiPost('/submit/url/', {
    content_id: contentId,
    content_type: contentType,
    additional_fields: additionalFields,
    content_url: content,
  });
}

export async function submitContentViaPostURLUpload(
  contentId,
  contentType,
  additionalFields,
  content,
) {
  const submitResponse = await apiPost('/submit/post_url/', {
    content_id: contentId,
    content_type: contentType,
    additional_fields: additionalFields,
    file_type: content.type,
  });

  const requestOptions = {
    method: 'PUT',
    body: content,
  };

  // Content object was created. Now the content itself needs to be uploaded to s3
  // using the post url in the response.
  const result = await fetch(submitResponse.presigned_url, requestOptions);
  return result;
}

export function fetchAllDatasets() {
  return apiGet('/datasets/');
}

export function syncAllDatasets() {
  return apiPost('/datasets/sync');
}

export function deleteDataset(key) {
  return apiPost(`/datasets/delete/${key}`);
}

export function updateDataset(
  privacyGroupId,
  fetcherActive,
  writeBack,
  matcherActive,
) {
  return apiPost('/datasets/update', {
    privacy_group_id: privacyGroupId,
    fetcher_active: fetcherActive,
    write_back: writeBack,
    matcher_active: matcherActive,
  });
}

export function createDataset(
  privacyGroupId,
  privacyGroupName,
  description = '',
  fetcherActive = false,
  writeBack = false,
  matcherActive = true,
) {
  return apiPost('/datasets/create', {
    privacy_group_id: privacyGroupId,
    privacy_group_name: privacyGroupName,
    description,
    fetcher_active: fetcherActive,
    write_back: writeBack,
    matcher_active: matcherActive,
  });
}

export function fetchHashCount() {
  return apiGet('/hash-counts');
}

// TODO remove the trailing slash from the API URL, then add back the leading slash for /actions/ and /action-rules/ endpoints.

export function fetchAllActions() {
  return apiGet('actions/');
}

export function createAction(newAction) {
  return apiPost('actions/', newAction);
}

export function updateAction(name, type, updatedAction) {
  return apiPut(`actions/${name}/${type}`, updatedAction);
}

export function deleteAction(name) {
  return apiDelete(`actions/${name}`);
}

export function fetchAllActionRules() {
  return apiGet('action-rules/');
}

export function addActionRule(actionRule) {
  return apiPost('action-rules/', {
    action_rule: actionRule,
  });
}

export function updateActionRule(oldName, actionRule) {
  return apiPut(`action-rules/${oldName}`, {
    action_rule: actionRule,
  });
}

export function deleteActionRule(name) {
  return apiDelete(`action-rules/${name}`);
}
