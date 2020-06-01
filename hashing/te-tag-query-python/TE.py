# ================================================================
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
# ================================================================

# General Python dependencies
import os
import urllib
import urllib.parse
import urllib.request
import urllib.error
import json
import copy

# ================================================================
# HTTP-wrapper methods
# See also https://developers.facebook.com/docs/threat-exchange

# This is a class with all static methods -- no need to instantiate it.  I
# meant it to be just a module but ran into an implementation detail with
# updating module-private variables in Python; ended up just making it a class.

class Net:
  THREAT_DESCRIPTOR = "THREAT_DESCRIPTOR";
  DEFAULT_TE_BASE_URL = "https://graph.facebook.com/v6.0"
  TE_BASE_URL = DEFAULT_TE_BASE_URL
  APP_TOKEN = None

  # This is just a keystroke-saver / error-avoider for passing around
  # post-parameter field names.

  POST_PARAM_NAMES = {
    'indicator'                          : 'indicator',     # For submit
    'type'                               : 'type',          # For submit
    'descriptor_id'                      : 'descriptor_id', # For update
  
    'description'                        : 'description',
    'share_level'                        : 'share_level',
    'status'                             : 'status',
    'privacy_type'                       : 'privacy_type',
    'privacy_members'                    : 'privacy_members',
    'tags'                               : 'tags',
    'add_tags'                           : 'add_tags',
    'remove_tags'                        : 'remove_tags',
    'confidence'                         : 'confidence',
    'precision'                          : 'precision',
    'review_status'                      : 'review_status',
    'severity'                           : 'severity',
    'expired_on'                         : 'expired_on',
    'first_active'                       : 'first_active',
    'last_active'                        : 'last_active',
    'related_ids_for_upload'             : 'related_ids_for_upload',
    'related_triples_for_upload_as_json' : 'related_triples_for_upload_as_json',
    # Legacy : should have been named reactions_to_add, but isn't. :(
    'reactions'                          : 'reactions',
    'reactions_to_remove'                : 'reactions_to_remove',
  }

  # ----------------------------------------------------------------
  # E.g. for overridiing
  #   https://graph.facebook.com/v{i}.{j}
  # to
  #   https://graph.facebook.com/v{x}.{y}
  @classmethod
  def setTEBaseURL(self, baseURL):
    self.DEFAULT_TE_BASE_URL = baseURL

  # ----------------------------------------------------------------
  # Gets the ThreatExchange app token from an environment variable.  Feel
  # free to replace the app-token discovery method here with whatever is
  # most convenient for your project. However, be aware that app tokens
  # are like passwords and shouldn't be stored in the open.

  # I like to put export TX_ACCESS_TOKEN=$(cat ~/.txtoken) in my .bashrc where
  # ~/.txtoken is a mode-600 file.
  @classmethod
  def setAppTokenFromEnvName(self, appTokenEnvName):
    if appTokenEnvName in os.environ:
      self.APP_TOKEN = os.environ[appTokenEnvName]
    else:
      raise Exception("$%s not found in environment." % appTokenEnvName)

  # ----------------------------------------------------------------
  # Helper method for issuing a GET and returning the JSON payload.
  @classmethod
  def getJSONFromURL(self, url):
    # The timeout is a heuristic
    response = urllib.request.urlopen(url, None, 60)
    # This is a Python 'bytes'
    response = response.read()
    # Now make it a string
    response = response.decode("utf-8")
    return json.loads(response)

  # ----------------------------------------------------------------
  # Looks up the "objective tag" ID for a given tag. This is suitable input for the /threat_tags endpoint.

  @classmethod
  def getTagIDFromName(self, tagName, showURLs = False):
    url = self.TE_BASE_URL + \
      "/threat_tags" + \
      "/?access_token=" + self.APP_TOKEN + \
      "&text=" + urllib.parse.quote(tagName)
    if showURLs:
      print("URL:")
      print(url)

    response = self.getJSONFromURL(url)

    # The lookup will get everything that has this as a prefix.
    # So we need to filter the results. This loop also handles the
    # case when the results array is empty.
    #
    # Example: when querying for "media_type_video", we want the 2nd one:
    # { "data": [
    #   { "id": "9999338563303771", "text": "media_type_video_long_hash" },
    #   { "id": "9999474908560728", "text": "media_type_video" },
    #   { "id": "9889872714202918", "text": "media_type_video_hash_long" }
    #   ], ...
    # }
    data = response['data']
    desired = list(filter(lambda o: o['text'] == tagName, data))
    if len(desired) < 1:
      return None
    else:
      return desired[0]['id']


  # ----------------------------------------------------------------
  # Looks up all descriptors with a given tag. Invokes a specified callback on
  # each page of IDs.

  @classmethod
  def processDescriptorIDsByTagID(self, tagID, idProcessorCallback, **kwargs):
    verbose = kwargs.get('verbose', False)
    showURLs = kwargs.get('showURLs', False)
    includeIndicatorInOutput = kwargs.get('includeIndicatorInOutput', True)
    pageSize = kwargs.get('pageSize', 10)
    taggedSince = kwargs.get('taggedSince', None)
    taggedUntil = kwargs.get('taggedUntil', None)

    startURL = self.TE_BASE_URL + \
      "/" + tagID + "/tagged_objects" + \
      "/?access_token=" + self.APP_TOKEN + \
      "&limit=" + str(pageSize)

    if taggedSince != None:
      startURL += "&tagged_since=" + taggedSince
    if taggedUntil != None:
      startURL += "&tagged_until=" + taggedUntil

    nextURL = startURL
    pageIndex = 0;

    while nextURL != None:
      if showURLs:
        print("URL:")
        print(nextURL)

      # Format we're parsing:
      # {
      #   "data": [
      #     {
      #       "id": "9915337796604770",
      #       "type": "THREAT_DESCRIPTOR",
      #       "name": "7ef5...aa97"
      #     }
      #     ...
      #   ],
      #   "paging": {
      #     "cursors": {
      #       "before": "XYZIU...NjQ0h3Unh3",
      #       "after": "XYZIUk...FXNzVNd1Jn"
      #     },
      #     "next": "https://graph.facebook.com/v3.1/9999338387644295/tagged_objects?access_token=..."
      #   }
      # }

      response = self.getJSONFromURL(nextURL)

      data = response['data']

      nextURL = None
      if 'paging' in response:
        paging = response['paging']
        if 'next' in paging:
          nextURL = paging['next']
      ids = []
      for item in data:
        itemID = item['id']
        itemType = item['type']
        if includeIndicatorInOutput:
          itemName = item['name']
        else:
          del item['name']
        if itemType != self.THREAT_DESCRIPTOR:
          continue
        if verbose:
          print(json.dumps(item))
        ids.append(itemID)
      if verbose:
        info = {}
        info['page_index'] = pageIndex
        info['num_items_pre_filter'] = len(data)
        info['num_items_post_filter'] = len(ids)
        print(json.dumps(info))

      idProcessorCallback(ids)

      pageIndex += 1


  # ----------------------------------------------------------------
  # Looks up all metadata for given IDs.
  @classmethod
  def getInfoForIDs(self, ids, **kwargs):
    verbose = kwargs.get('verbose', False)
    showURLs = kwargs.get('showURLs', False)
    includeIndicatorInOutput = kwargs.get('includeIndicatorInOutput', True)

    # Check well-formattedness of descriptor IDs (which may have come from
    # arbitrary data on stdin).
    for id in ids:
      try:
        _ = int(id)
      except ValueError:
        raise Exception("Malformed descriptor ID \"%s\"" % id)

    # See also
    # https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-descriptor/v6.0
    # for available fields

    url = self.TE_BASE_URL + \
      "/?access_token=" + self.APP_TOKEN + \
      "&ids=" + ','.join(ids) + \
      "&fields=raw_indicator,type,added_on,last_updated,confidence,owner,privacy_type,review_status,status,severity,share_level,tags,description,reactions,my_reactions"

    if showURLs:
      print("URL:")
      print(url)

    response = self.getJSONFromURL(url)

    descriptors = []
    for id, descriptor in response.items():
      if includeIndicatorInOutput == False:
        del descriptor['raw_indicator']
      if verbose:
        print(json.dumps(descriptor))

      tags = descriptor.get('tags', None)
      if tags is None:
        tags = []
      else:
        tags = tags['data']

      # Canonicalize the tag ordering and simplify the
      # structure to simply an array of tag-texts
      descriptor['tags'] = [tag['text'] for tag in tags].sort()

      if descriptor.get('description') is None:
        descriptor['description'] = ''

      descriptors.append(descriptor)

    return descriptors

  # ----------------------------------------------------------------
  # Returns error message or None.
  # This simply checks to see (client-side) if required fields aren't provided.
  @classmethod
  def validatePostPararmsForSubmit(self, postParams):
    if postParams.get(self.POST_PARAM_NAMES['descriptor_id']) != None:
      return "descriptor_id must not be specified for submit."

    requiredFields = [
      self.POST_PARAM_NAMES['indicator'],
      self.POST_PARAM_NAMES['type'],
      self.POST_PARAM_NAMES['description'],
      self.POST_PARAM_NAMES['share_level'],
      self.POST_PARAM_NAMES['status'],
      self.POST_PARAM_NAMES['privacy_type'],
    ]

    missingFields = [
      fieldName if postParams.get(fieldName) == None  else None
      for fieldName in requiredFields
    ]
    missingFields = [fieldName for fieldName in missingFields if fieldName != None]

    if len(missingFields) == 0:
      return None
    elif len(missingFields) == 1:
      return "Missing field %s" % missingFields[0]
    else:
      return "Missing fields %s" % ','.join(missingFields)


  # ----------------------------------------------------------------
  # Returns error message or None.
  # This simply checks to see (client-side) if required fields aren't provided.
  @classmethod
  def validatePostPararmsForUpdate(self, postParams):
    if postParams.get(self.POST_PARAM_NAMES['descriptor_id']) == None:
      return "Descriptor ID must be specified for update."
    if postParams.get(self.POST_PARAM_NAMES['indicator']) != None:
      return "Indicator must not be specified for update."
    if postParams.get(self.POST_PARAM_NAMES['type']) != None:
      return "Type must not be specified for update."
    return None

  # ----------------------------------------------------------------
  # Returns error message or None.
  # This simply checks to see (client-side) if required fields aren't provided.
  @classmethod
  def validatePostPararmsForCopy(self, postParams):
    if postParams.get(self.POST_PARAM_NAMES['descriptor_id']) == None:
      return "Source-descriptor ID must be specified for update."
    return None


  # ----------------------------------------------------------------
  # Does a single POST to the threat_descriptors endpoint.  See also
  # https://developers.facebook.com/docs/threat-exchange/reference/submitting
  @classmethod
  def submitThreatDescriptor(self, postParams, showURLs, dryRun):
    errorMessage = self.validatePostPararmsForSubmit(postParams)
    if errorMessage != None:
      return [errorMessage, None, None]

    url = self.TE_BASE_URL + \
      "/threat_descriptors" + \
      "/?access_token=" + self.APP_TOKEN

    return self._postThreatDescriptor(url, postParams, showURLs, dryRun)

  # ----------------------------------------------------------------
  # Does a single POST to the threat_descriptor ID endpoint.  See also
  # https://developers.facebook.com/docs/threat-exchange/reference/editing
  @classmethod
  def updateThreatDescriptor(self, postParams, showURLs, dryRun):
    errorMessage = self.validatePostPararmsForUpdate(postParams)
    if errorMessage != None:
      return [errorMessage, None, None]

    url = self.TE_BASE_URL + \
      "/" + postParams[self.POST_PARAM_NAMES['descriptor_id']] + \
      "/?access_token=" + self.APP_TOKEN

    return self._postThreatDescriptor(url, postParams, showURLs, dryRun)

  # ----------------------------------------------------------------
  # xxx
  @classmethod
  def copyThreatDescriptor(self, postParams, showURLs, dryRun):
    errorMessage = self.validatePostPararmsForCopy(postParams)
    if errorMessage != None:
      return [errorMessage, None, None]

    # Get source descriptor
    sourceID = postParams['descriptor_id']
    del postParams['descriptor_id']
    sourceDescriptor = self.getInfoForIDs([sourceID], showURLs=showURLs)
    sourceDescriptor = sourceDescriptor[0]
    # xxx check for non-null/whatever ... try/catch maybe ...

    # Mutate necessary fields
    # xxx transmogrify -- raw_indicator -> indicator -- what else?
    newDescriptor = copy.deepcopy(sourceDescriptor)
    newDescriptor['indicator'] = sourceDescriptor['raw_indicator']
    del newDescriptor['raw_indicator']
    if 'tags' in newDescriptor and newDescriptor['tags'] is None:
      del newDescriptor['tags']


    # Take the source-descriptor values and overwrite any post-params fields
    # supplied by the caller. Note: Python's dict-update method keeps the old
    # value for a given field name when both old and new are present so we
    # invoke it seemingly 'backward'.
    #
    # Example:
    # * x = {'a': 1, 'b': 2, 'c': 3}
    # * y = {'a': 1, 'b': 9, 'd': 12}
    # * After y.update(x) then x is unchanged and y is
    #       {'a': 1, 'b': 2, 'd': 12, 'c': 3}
    #
    # This means we want newDescriptor.update(postParams)
    newDescriptor.update(postParams)

    # Get rid of fields like last_upated from the source descriptor which
    # aren't valid for post
    postParams = {}
    for key, value in newDescriptor.items():
      if self.POST_PARAM_NAMES.get(key) != None:
        postParams[key] = value

    # xxx privacy_members -- underdiff

    return self.submitThreatDescriptor(postParams, showURLs, dryRun)


  # ----------------------------------------------------------------
  # Code-reuse for submit and update
  @classmethod
  def _postThreatDescriptor(self, url, postParams, showURLs, dryRun):
    for key, value in postParams.items():
      url += ("&%s=%s" % (key, urllib.parse.quote(str(value))))
    if showURLs:
      print()
      print("URL:")
      print(url)
    if (dryRun):
      print("Not doing POST since --dry-run.")
      return [None, None, '']

    # Encode the inputs to the POST
    header = {
      'Content-Type':  'text/json',
      'charset': 'utf-8',
    }
    # This is a string
    data = urllib.parse.urlencode(postParams)
    # Turn it into a Python bytes object
    data = data.encode('ascii')

    # Do the POST
    try:
      response = urllib.request.urlopen(url, data)

      # Decode the outputs from the POST
      # This is a Python 'bytes'
      response = response.read()
      # Now make it a string
      response = response.decode("utf-8")
      responseBody = json.loads(response)
      responseCode = None

      return [None, None, responseBody]

    # xxx code ...
    except urllib.error.HTTPError as e:
      responseBody = json.loads(e.read().decode("utf-8"))
      return [None, e, responseBody]
