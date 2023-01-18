// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

package com.facebook.threatexchange;

import java.io.PrintStream;
import java.net.URL;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Stream;

/**
 * Helper container class for posting threat descriptors to ThreatExchange.
 */
public class DescriptorPostParameters {
  private String _indicatorText; // Required for submit
  private String _indicatorType; // Required for submit
  private String _descriptorID;  // Required for update
  private String _description;
  private String _shareLevel;
  private String _status;
  private String _privacyType;
  // If privacy_type is HAS_WHITELIST these must be app IDs.
  // If privacy_type is HAS_PRIVACY_GROUP these must be privacy-group IDs.
  private String _privacyMembers;

  private String _confidence;
  private String _precision;
  private String _reviewStatus;
  private String _severity;
  private String _expiredOn;
  private String _firstActive;
  private String _lastActive;
  private String _tagsToSet;
  private String _tagsToAdd;
  private String _tagsToRemove;
  private String _relatedIDsForUpload;
  private String _relatedTriplesForUploadAsJSON;
  private String _reactionsToAdd;
  private String _reactionsToRemove;

  public DescriptorPostParameters setIndicatorText(String indicatorText) {
    this._indicatorText = indicatorText;
    return this;
  }
  public DescriptorPostParameters setIndicatorType(String indicatorType) {
    this._indicatorType = indicatorType;
    return this;
  }
  public DescriptorPostParameters setDescriptorID(String descriptorID) {
    this._descriptorID = descriptorID;
    return this;
  }
  public DescriptorPostParameters setDescription(String description) {
    this._description = description;
    return this;
  }
  public DescriptorPostParameters setShareLevel(String shareLevel) {
    this._shareLevel = shareLevel;
    return this;
  }
  public DescriptorPostParameters setStatus(String status) {
    this._status = status;
    return this;
  }
  public DescriptorPostParameters setPrivacyType(String privacyType) {
    this._privacyType = privacyType;
    return this;
  }
  public DescriptorPostParameters setPrivacyMembers(String privacyMembers) {
    this._privacyMembers = privacyMembers;
    return this;
  }
  public DescriptorPostParameters setConfidence(String confidence) {
    this._confidence = confidence;
    return this;
  }
  public DescriptorPostParameters setPrecision(String precision) {
    this._precision = precision;
    return this;
  }
  public DescriptorPostParameters setReviewStatus(String reviewStatus) {
    this._reviewStatus = reviewStatus;
    return this;
  }
  public DescriptorPostParameters setSeverity(String severity) {
    this._severity = severity;
    return this;
  }
  public DescriptorPostParameters setExpiredOn(String expiredOn) {
    this._expiredOn = expiredOn;
    return this;
  }
  public DescriptorPostParameters setFirstActive(String firstActive) {
    this._firstActive = firstActive;
    return this;
  }
  public DescriptorPostParameters setLastActive(String lastActive) {
    this._lastActive = lastActive;
    return this;
  }
  public DescriptorPostParameters setTagsToSet(String tagsToSet) {
    this._tagsToSet = tagsToSet;
    return this;
  }
  public DescriptorPostParameters setTagsToAdd(String tagsToAdd) {
    this._tagsToAdd = tagsToAdd;
    return this;
  }
  public DescriptorPostParameters setTagsToRemove(String tagsToRemove) {
    this._tagsToRemove = tagsToRemove;
    return this;
  }
  public DescriptorPostParameters setRelatedIDsForUpload(String relatedIDsForUpload) {
    this._relatedIDsForUpload = relatedIDsForUpload;
    return this;
  }
  public DescriptorPostParameters setRelatedTriplesForUploadAsJSON(String relatedTriplesForUploadAsJSON) {
    this._relatedTriplesForUploadAsJSON = relatedTriplesForUploadAsJSON;
    return this;
  }
  public DescriptorPostParameters setReactionsToAdd(String reactionsToAdd) {
    this._reactionsToAdd = reactionsToAdd;
    return this;
  }
  public DescriptorPostParameters setReactionsToRemove(String reactionsToRemove) {
    this._reactionsToRemove = reactionsToRemove;
    return this;
  }

  public DescriptorPostParameters ifNotNullSetIndicatorText(String indicatorText) {
    if (indicatorText != null) {
      return setIndicatorText(indicatorText);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetIndicatorType(String indicatorType) {
    if (indicatorType != null) {
      return setIndicatorType(indicatorType);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetDescriptorID(String descriptorID) {
    if (descriptorID != null) {
      return setDescriptorID(descriptorID);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetDescription(String description) {
    if (description != null) {
      return setDescription(description);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetShareLevel(String shareLevel) {
    if (shareLevel != null) {
      return setShareLevel(shareLevel);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetStatus(String status) {
    if (status != null) {
      return setStatus(status);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetPrivacyType(String privacyType) {
    if (privacyType != null) {
      return setPrivacyType(privacyType);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetPrivacyMembers(String privacyMembers) {
    if (privacyMembers != null) {
      return setPrivacyMembers(privacyMembers);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetConfidence(String confidence) {
    if (confidence != null) {
      return setConfidence(confidence);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetPrecision(String precision) {
    if (precision != null) {
      return setPrecision(precision);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetReviewStatus(String reviewStatus) {
    if (reviewStatus != null) {
      return setReviewStatus(reviewStatus);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetSeverity(String severity) {
    if (severity != null) {
      return setSeverity(severity);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetExpiredOn(String expiredOn) {
    if (expiredOn != null) {
      return setExpiredOn(expiredOn);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetFirstActive(String firstActive) {
    if (firstActive != null) {
      return setFirstActive(firstActive);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetLastActive(String lastActive) {
    if (lastActive != null) {
      return setLastActive(lastActive);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetTagsToSet(String tagsToSet) {
    if (tagsToSet != null) {
      return setTagsToSet(tagsToSet);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetTagsToAdd(String tagsToAdd) {
    if (tagsToAdd != null) {
      return setTagsToAdd(tagsToAdd);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetTagsToRemove(String tagsToRemove) {
    if (tagsToRemove != null) {
      return setTagsToRemove(tagsToRemove);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetRelatedIDsForUpload(String relatedIDsForUpload) {
    if (relatedIDsForUpload != null) {
      return setRelatedIDsForUpload(relatedIDsForUpload);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetRelatedTriplesForUploadAsJSON(String relatedTriplesForUploadAsJSON) {
    if (relatedTriplesForUploadAsJSON != null) {
      return setRelatedTriplesForUploadAsJSON(relatedTriplesForUploadAsJSON);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetReactionsToAdd(String reactionsToAdd) {
    if (reactionsToAdd != null) {
      return setReactionsToAdd(reactionsToAdd);
    }
    return this;
  }
  public DescriptorPostParameters ifNotNullSetReactionsToRemove(String reactionsToRemove) {
    if (reactionsToRemove != null) {
      return setReactionsToRemove(reactionsToRemove);
    }
    return this;
  }

  public String getIndicatorText() {
    return this._indicatorText;
  }
  public String getIndicatorType() {
    return this._indicatorType;
  }
  public String getDescriptorID() {
    return this._descriptorID;
  }
  public String getDescription() {
    return this._description;
  }
  public String getShareLevel() {
    return this._shareLevel;
  }
  public String getStatus() {
    return this._status;
  }
  public String getPrivacyType() {
    return this._privacyType;
  }
  public String getPrivacyMembers() {
    return this._privacyMembers;
  }
  public String getConfidence() {
    return this._confidence;
  }
  public String getPrecision() {
    return this._precision;
  }
  public String getReviewStatus() {
    return this._reviewStatus;
  }
  public String getSeverity() {
    return this._severity;
  }
  public String getExpiredOn() {
    return this._expiredOn;
  }
  public String getFirstActive() {
    return this._firstActive;
  }
  public String getLastActive() {
    return this._lastActive;
  }
  public String getTagsToSet() {
    return this._tagsToSet;
  }
  public String getTagsToAdd() {
    return this._tagsToAdd;
  }
  public String getTagsToRemove() {
    return this._tagsToRemove;
  }
  public String getRelatedIDsForUpload() {
    return this._relatedIDsForUpload;
  }
  public String getRelatedTriplesForUploadAsJSON() {
    return this._relatedTriplesForUploadAsJSON;
  }
  public String getReactionsToAdd() {
    return this._reactionsToAdd;
  }
  public String getReactionsToRemove() {
    return this._reactionsToRemove;
  }

  // Returns null if no errors, non-null for error.
  public String validateForSubmitWithReport() {
    if (this._descriptorID != null) {
      return "Descriptor ID must not be specified for submit.";
    }
    if (this._indicatorText == null) {
      return "Indicator text must be specified for submit.";
    }
    if (this._indicatorType == null) {
      return "Indicator type must be specified for submit.";
    }
    if (this._description == null) {
      return "Description must be specified for submit.";
    }
    if (this._shareLevel == null) {
      return "Share level must be specified for submit.\n";
    }
    if (this._status == null) {
      return "Status must be specified for submit.\n";
    }
    if (this._privacyType == null) {
      return "Privacy type must be specified for submit.\n";
    }
    return null;
  }

  // Returns null if no errors, non-null for error.
  public String validateForUpdateWithReport() {
    if (this._descriptorID == null) {
      return "Descriptor ID must be specified for update.";
    }
    if (this._indicatorText != null) {
      return "Indicator text must not be specified for update.";
    }
    if (this._indicatorType != null) {
      return "Indicator type must not be specified for update.";
    }
    return null;
  }

  // Returns null if no errors, non-null for error.
  public String validateForCopyWithReport() {
    if (this._descriptorID == null) {
      return "Descriptor ID must be specified for copy.";
    }
    if (this._privacyMembers == null) {
      return "Privacy members must be specified for copy.";
    }
    if (this._privacyType == null) {
      return "Privacy type must be specified for copy.";
    }
    return null;
  }

  // URL-encode since data is user-provided.
  // Assumes the input is already validated (non-null indicator text/type etc.)
  public String getPostDataString() {
    StringBuilder sb = new StringBuilder();
    if (this._indicatorType != null) {
      sb.append("type=").append(Utils.urlEncodeUTF8(this._indicatorType));
    }
    if (this._description != null) {
      sb.append("&description=").append(Utils.urlEncodeUTF8(this._description));
    }
    if (this._shareLevel != null) {
      sb.append("&share_level=").append(Utils.urlEncodeUTF8(this._shareLevel));
    }
    if (this._status != null) {
      sb.append("&status=").append(Utils.urlEncodeUTF8(this._status));
    }
    if (this._privacyType != null) {
      sb.append("&privacy_type=").append(Utils.urlEncodeUTF8(this._privacyType));
    }
    if (this._privacyMembers != null) {
      sb.append("&privacy_members=").append(Utils.urlEncodeUTF8(this._privacyMembers));
    }
    if (this._tagsToSet != null) {
      sb.append("&tags=").append(Utils.urlEncodeUTF8(this._tagsToSet));
    }
    if (this._tagsToAdd != null) {
      sb.append("&add_tags=").append(Utils.urlEncodeUTF8(this._tagsToAdd));
    }
    if (this._tagsToRemove != null) {
      sb.append("&remove_tags=").append(Utils.urlEncodeUTF8(this._tagsToRemove));
    }
    if (this._confidence != null) {
      sb.append("&confidence=").append(Utils.urlEncodeUTF8(this._confidence));
    }
    if (this._precision != null) {
      sb.append("&precision=").append(Utils.urlEncodeUTF8(this._precision));
    }
    if (this._reviewStatus != null) {
      sb.append("&review_status=").append(Utils.urlEncodeUTF8(this._reviewStatus));
    }
    if (this._severity != null) {
      sb.append("&severity=").append(Utils.urlEncodeUTF8(this._severity));
    }
    if (this._expiredOn != null) {
      sb.append("&expired_on=").append(Utils.urlEncodeUTF8(this._expiredOn));
    }
    if (this._firstActive != null) {
      sb.append("&first_active=").append(Utils.urlEncodeUTF8(this._firstActive));
    }
    if (this._lastActive != null) {
      sb.append("&last_active=").append(Utils.urlEncodeUTF8(this._tagsToRemove));
    }
    if (this._relatedIDsForUpload != null) {
      sb.append("&related_ids_for_upload=").append(Utils.urlEncodeUTF8(this._relatedIDsForUpload));
    }
    if (this._relatedTriplesForUploadAsJSON != null) {
      sb.append("&related_triples_for_upload_as_json=")
        .append(Utils.urlEncodeUTF8(this._relatedTriplesForUploadAsJSON));
    }
    if (this._reactionsToAdd != null) {
      sb.append("&reactions=").append(Utils.urlEncodeUTF8(this._reactionsToAdd));
    }
    if (this._reactionsToRemove != null) {
      sb.append("&reactions_to_remove=").append(Utils.urlEncodeUTF8(this._reactionsToRemove));
    }
    // Put indicator last in case it's long (e.g. TMK) for human readability
    if (this._indicatorText != null) {
      sb.append("&indicator=").append(Utils.urlEncodeUTF8(this._indicatorText));
    }
    return sb.toString();
  }
}
