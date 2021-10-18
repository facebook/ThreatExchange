/**
 * Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
 */

import {Auth, API} from 'aws-amplify';
import {ActionRule, Label} from './pages/settings/ActionRuleSettingsTab';
import {Action} from './pages/settings/ActionSettingsTab';
import {Bank, BankMember} from './messages/BankMessages';
import {toDate} from './utils/DateTimeUtils';
import {ContentType, getContentTypeForString} from './utils/constants';

async function getAuthorizationToken(): Promise<string> {
  const currentSession = await Auth.currentSession();
  const accessToken = currentSession.getAccessToken();
  const jwtToken = accessToken.getJwtToken();
  return jwtToken;
}

async function apiGet<T>(
  route: string,
  params = {},
  responseType = null,
): Promise<T> {
  return API.get('hma_api', route, {
    responseType,
    headers: {
      Authorization: await getAuthorizationToken(),
    },
    queryStringParameters: params,
  });
}

async function apiPost<T>(route: string, body = {}, params = {}): Promise<T> {
  return API.post('hma_api', route, {
    body,
    headers: {
      Authorization: await getAuthorizationToken(),
    },
    queryStringParameters: params,
  });
}

async function apiPut<T>(route: string, body = {}, params = {}): Promise<T> {
  return API.put('hma_api', route, {
    body,
    headers: {
      Authorization: await getAuthorizationToken(),
    },
    queryStringParameters: params,
  });
}

async function apiDelete<T>(route: string, params = {}): Promise<T> {
  return API.del('hma_api', route, {
    headers: {
      Authorization: await getAuthorizationToken(),
    },
    queryStringParameters: params,
  });
}

type MatchSummaries = {match_summaries: MatchDetails[]};

export async function fetchAllMatches(): Promise<MatchSummaries> {
  return apiGet('matches/');
}

export async function fetchMatchesFromSignal(
  signalSource: string,
  signalId: string,
): Promise<MatchSummaries> {
  return apiGet('matches/', {
    signal_q: signalId,
    signal_source: signalSource,
  });
}

export async function fetchMatchesFromContent(
  contentId: string,
): Promise<MatchSummaries> {
  return apiGet('matches/', {content_q: contentId});
}

export type MatchDetails = {
  content_id: string;
  content_hash: string;
  signal_id: string;
  signal_hash: string;
  signal_source: string;
  signal_type: string;
  updated_at: string;
  metadata: {
    privacy_group_id: string;
    tags: string[];
    opinion: string;
    pending_opinion_change: string;
  }[];
};

type Matches = {match_details: MatchDetails[]};

export async function fetchMatchDetails(contentId: string): Promise<Matches> {
  return apiGet('matches/match/', {content_id: contentId});
}

export type HashDetails = {
  content_hash: string;
  updated_at: string;
};

export async function fetchHashDetails(
  contentId: string,
): Promise<HashDetails> {
  return apiGet('content/hash/', {content_id: contentId});
}

export async function fetchPreviewURL(
  contentId: string,
): Promise<{preview_url: string}> {
  return apiGet('content/preview-url/', {content_id: contentId});
}

export type ContentActionHistoryRecord = {
  action_label: string;
  performed_at: string;
};

type ContentActionHistoryRecords = {
  action_history: Array<ContentActionHistoryRecord>;
};

export async function fetchContentActionHistory(
  contentId: string,
): Promise<ContentActionHistoryRecords> {
  return apiGet('content/action-history/', {content_id: contentId});
}

export type ContentDetails = {
  content_id: string;
  content_type: string;

  content_ref: string;
  content_ref_type: string;

  submission_times: Array<string>;

  created_at: string;
  updated_at: string;
  additional_fields: Array<string>;
};

export async function fetchContentDetails(
  contentId: string,
): Promise<ContentDetails> {
  return apiGet('content/', {
    content_id: contentId,
  });
}

type ContentPipelineProgress = {
  content_type: string;
  content_preview_url: string;
  submitted_at: string;
  hashed_at: string;
  matched_at: string;
  action_evaluated_at: string;
  action_performed_at: string;
};

export async function fetchContentPipelineProgress(
  contentId: string,
): Promise<ContentPipelineProgress> {
  return apiGet('content/pipeline-progress/', {
    content_id: contentId,
  });
}

export async function fetchDashboardCardSummary(
  path: string,
): Promise<Response> {
  return apiGet(`${path}`);
}

export type StatsCard = {
  time_span_count: number;
  time_span: string;
  graph_data: Array<[number, number]>;
  last_updated: string;
};

type StatsResponse = {
  card: StatsCard;
};

export async function fetchStats(
  statName: string,
  timeSpan: string,
): Promise<StatsResponse> {
  return apiGet('stats/', {stat_name: statName, time_span: timeSpan});
}

export async function requestSignalOpinionChange(
  signalId: string,
  signalSource: string,
  privacyGroupId: string,
  opinionChange: string,
): Promise<void> {
  apiPost(
    '/matches/request-signal-opinion-change/',
    {},
    {
      signal_id: signalId,
      signal_source: signalSource,
      privacy_group_id: privacyGroupId,
      opinion_change: opinionChange,
    },
  );
}

export async function submitContentViaURL(
  contentId: string,
  contentType: string,
  additionalFields: string[],
  contentURL: string,
  forceResubmit: boolean,
): Promise<Response> {
  return apiPost('submit/url/', {
    content_id: contentId,
    content_type: contentType,
    additional_fields: additionalFields,
    content_url: contentURL,
    force_resubmit: forceResubmit,
  });
}

export async function submitContentViaPutURLUpload(
  contentId: string,
  contentType: string,
  additionalFields: string[],
  content: File,
  forceResubmit: boolean,
): Promise<Response> {
  const submitResponse = await apiPost<{presigned_url: string}>(
    'submit/put-url/',
    {
      content_id: contentId,
      content_type: contentType,
      additional_fields: additionalFields,
      file_type: content.type,
      force_resubmit: forceResubmit,
    },
  );

  const requestOptions = {
    method: 'PUT',
    body: content,
  };

  // Content object was created. Now the content itself needs to be uploaded to s3
  // using the put url in the response.
  const result = await fetch(submitResponse.presigned_url, requestOptions);
  return result;
}

type DatasetSummariesResponse = {
  threat_exchange_datasets: Array<Dataset>;
};
export async function fetchAllDatasets(): Promise<DatasetSummariesResponse> {
  return apiGet('datasets/');
}

export async function syncAllDatasets(): Promise<{response: string}> {
  return apiPost('datasets/sync');
}

export async function deleteDataset(key: string): Promise<{response: string}> {
  return apiPost(`datasets/delete/${key}`);
}

export type PrivacyGroup = {
  privacyGroupId: string;
  localFetcherActive: boolean;
  localWriteBack: boolean;
  localMatcherActive: boolean;
};

type Dataset = {
  privacy_group_id: string;
  privacy_group_name: string;
  description: string;
  fetcher_active: boolean;
  matcher_active: boolean;
  write_back: boolean;
  in_use: boolean;
  hash_count: number;
  match_count: number;
};

export async function updateDataset(
  privacyGroupId: string,
  fetcherActive: boolean,
  writeBack: boolean,
  matcherActive: boolean,
): Promise<Dataset> {
  return apiPost('datasets/update', {
    privacy_group_id: privacyGroupId,
    fetcher_active: fetcherActive,
    write_back: writeBack,
    matcher_active: matcherActive,
  });
}

export async function createDataset(
  privacyGroupId: string,
  privacyGroupName: string,
  description = '',
  fetcherActive = false,
  writeBack = false,
  matcherActive = true,
): Promise<{response: string}> {
  return apiPost('datasets/create', {
    privacy_group_id: privacyGroupId,
    privacy_group_name: privacyGroupName,
    description,
    fetcher_active: fetcherActive,
    write_back: writeBack,
    matcher_active: matcherActive,
  });
}

export async function fetchHashCount(): Promise<Response> {
  return apiGet('hash-counts');
}

// This class should be kept in sync with python class ActionPerformer (hmalib.common.configs.actioner.ActionPerformer)
type BackendActionPerformer = {
  name: string;
  config_subtype: string;
  url: string;
  headers: string;
};

type AllActions = {
  error_message: string;
  actions_response: Array<BackendActionPerformer>;
};

export async function fetchAllActions(): Promise<Action[]> {
  return apiGet<AllActions>('actions/').then(response => {
    if (response && !response.error_message && response.actions_response) {
      return response.actions_response.map(
        action =>
          ({
            name: action.name,
            config_subtype: action.config_subtype,
            params: {url: action.url, headers: action.headers},
          } as Action),
      );
    }
    return [];
  });
}

export async function createAction(
  newAction: Action,
): Promise<{response: string}> {
  return apiPost('actions/', {
    name: newAction.name,
    config_subtype: newAction.config_subtype,
    fields: newAction.params,
  });
}

export async function updateAction(
  old_name: string,
  old_config_subtype: string,
  updatedAction: Action,
): Promise<{response: string}> {
  return apiPut(`actions/${old_name}/${old_config_subtype}`, {
    name: updatedAction.name,
    config_subtype: updatedAction.config_subtype,
    fields: updatedAction.params,
  });
}

export async function deleteAction(name: string): Promise<{response: string}> {
  return apiDelete(`actions/${name}`);
}

// We need two different ActionRule types because the mackend model (must (not) have labels) is different
// from the Frontend model (classification conditions).
// This class should be kept in sync with python class ActionRule (hmalib.common.configs.evaluator.ActionRule)
type BackendActionRule = {
  name: string;
  must_have_labels: Label[];
  must_not_have_labels: Label[];
  action_label: {
    key: string;
    value: string;
  };
};

const convertToBackendActionRule = (frontend_action_rule: ActionRule) =>
  ({
    name: frontend_action_rule.name,
    must_have_labels: frontend_action_rule.must_have_labels,
    must_not_have_labels: frontend_action_rule.must_not_have_labels,
    action_label: {
      key: 'Action',
      value: frontend_action_rule.action_name,
    },
  } as BackendActionRule);

type AllActionRules = {
  error_message: string;
  action_rules: Array<BackendActionRule>;
};

export async function fetchAllActionRules(): Promise<ActionRule[]> {
  return apiGet<AllActionRules>('action-rules/').then(response => {
    if (response && response.error_message === '' && response.action_rules) {
      const fetchedActionRules = response.action_rules.map(
        backend_action_rule =>
          new ActionRule(
            backend_action_rule.name,
            backend_action_rule.action_label.value,
            backend_action_rule.must_have_labels,
            backend_action_rule.must_not_have_labels,
          ),
      );
      return fetchedActionRules;
    }
    return [];
  });
}

export async function addActionRule(actionRule: ActionRule): Promise<Response> {
  const backendActionRule = convertToBackendActionRule(actionRule);
  return apiPost('action-rules/', {
    action_rule: backendActionRule,
  });
}

export async function updateActionRule(
  oldName: string,
  actionRule: ActionRule,
): Promise<Response> {
  const backendActionRule = convertToBackendActionRule(actionRule);
  return apiPut(`action-rules/${oldName}`, {
    action_rule: backendActionRule,
  });
}

export async function deleteActionRule(name: string): Promise<Response> {
  return apiDelete(`action-rules/${name}`);
}

// Banks APIs

type BankWithStringDates = Bank & {
  created_at: string;
  updated_at: string;
};

type AllBanksResponse = {
  banks: BankWithStringDates[];
};

export async function fetchAllBanks(): Promise<Bank[]> {
  return apiGet<AllBanksResponse>('banks/get-all-banks').then(response =>
    response.banks.map(item => ({
      bank_id: item.bank_id!,
      bank_name: item.bank_name!,
      bank_description: item.bank_description!,
      created_at: toDate(item.created_at)!,
      updated_at: toDate(item.updated_at)!,
    })),
  );
}

export async function fetchBank(bankId: string): Promise<Bank> {
  return apiGet<BankWithStringDates>(`banks/get-bank/${bankId}`).then(
    response => ({
      bank_id: response.bank_id!,
      bank_name: response.bank_name!,
      bank_description: response.bank_description!,
      created_at: toDate(response.created_at)!,
      updated_at: toDate(response.updated_at)!,
    }),
  );
}

export async function createBank(
  bankName: string,
  bankDescription: string,
): Promise<void> {
  return apiPost('banks/create-bank', {
    bank_name: bankName,
    bank_description: bankDescription,
  });
}

export async function updateBank(
  bankId: string,
  bankName: string,
  bankDescription: string,
): Promise<Bank> {
  return apiPost<BankWithStringDates>(`banks/update-bank/${bankId}`, {
    bank_name: bankName,
    bank_description: bankDescription,
  }).then(response => ({
    bank_id: response.bank_id!,
    bank_name: response.bank_name!,
    bank_description: response.bank_description!,
    created_at: toDate(response.created_at)!,
    updated_at: toDate(response.updated_at)!,
  }));
}

type BankMemberWithSerializedTypes = BankMember & {
  content_type: string;
  created_at: string;
  updated_at: string;
};

type BankMembersPage = {
  bank_members: BankMemberWithSerializedTypes[];
  continuation_token: string;
};

export async function fetchBankMembersPage(
  bankId: string,
  contentType: ContentType,
  continuationToken?: string,
): Promise<[BankMember[], string]> {
  const url =
    continuationToken === undefined
      ? `banks/get-members/${bankId}?content_type=${contentType}`
      : `banks/get-members/${bankId}?content_type=${contentType}&continuation_token=${continuationToken}`;
  return apiGet<BankMembersPage>(url).then(response => [
    response.bank_members.map(member => ({
      bank_id: member.bank_id,
      bank_member_id: member.bank_member_id,
      content_type: getContentTypeForString(member.content_type),
      storage_bucket: member.storage_bucket,
      storage_key: member.storage_key,
      raw_content: member.raw_content,
      preview_url: member.preview_url,
      notes: member.notes,
      created_at: toDate(member.created_at)!,
      updated_at: toDate(member.updated_at)!,
    })),
    response.continuation_token,
  ]);
}

type MediaUploadURLResponse = {
  upload_url: string;
  storage_bucket: string;
  storage_key: string;
};

export async function fetchMediaUploadURL(
  mediaType: string,
  extension: string,
): Promise<MediaUploadURLResponse> {
  return apiPost<MediaUploadURLResponse>('banks/get-media-upload-url', {
    media_type: mediaType,
    extension,
  });
}

export async function addBankMember(
  bankId: string,
  contentType: ContentType,
  storageBucket: string,
  storageKey: string,
  notes: string,
): Promise<BankMember> {
  return apiPost<BankMemberWithSerializedTypes>(`banks/add-member/${bankId}`, {
    content_type: contentType,
    storage_bucket: storageBucket,
    storage_key: storageKey,
    notes,
  }).then(response => ({
    bank_id: response.bank_id,
    bank_member_id: response.bank_member_id,
    content_type: getContentTypeForString(response.content_type),
    storage_bucket: response.storage_bucket,
    storage_key: response.storage_key,
    preview_url: response.preview_url,
    notes: response.notes,
    created_at: toDate(response.created_at)!,
    updated_at: toDate(response.updated_at)!,
  }));
}
