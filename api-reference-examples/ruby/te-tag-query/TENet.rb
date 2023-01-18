# ================================================================
# Copyright (c) Meta Platforms, Inc. and affiliates.
# ================================================================

# General Ruby dependencies
require 'cgi' # for URL-encoding
require 'net/http'
require 'uri'
require 'json'
require 'date'

# ================================================================
# HTTP-wrapper methods
# See also https://developers.facebook.com/docs/threat-exchange
module ThreatExchange
module TENet

DEFAULT_TE_BASE_URL = "https://graph.facebook.com/v6.0"
THREAT_DESCRIPTOR = "THREAT_DESCRIPTOR";

# This is just a keystroke-saver / error-avoider for passing around
# post-parameter field names.
POST_PARAM_NAMES = {
  :indicator                          => "indicator",    # For submit
  :type                               => "type",         # For submit
  :descriptor_id                      => "descriptor_id", # For update

  :description                        => "description",
  :share_level                        => "share_level",
  :status                             => "status",
  :privacy_type                       => "privacy_type",
  :privacy_members                    => "privacy_members",
  :tags                               => "tags",
  :add_tags                           => "add_tags",
  :remove_tags                        => "remove_tags",
  :confidence                         => "confidence",
  :precision                          => "precision",
  :review_status                      => "review_status",
  :severity                           => "severity",
  :expired_on                         => "expired_on",
  :first_active                       => "first_active",
  :last_active                        => "last_active",
  :related_ids_for_upload             => "related_ids_for_upload",
  :related_triples_for_upload_as_json => "related_triples_for_upload_as_json",
  # Legacy: should have been named reactions_to_add, but isn't. :(
  :reactions                          => "reactions",
  :reactions_to_remove                => "reactions_to_remove",
}
POST_PARAM_NAMES.default_proc = -> (h, k) { raise KeyError, "POST_PARAM_NAMES[#{k}] is not defined." }

STRING_POST_PARAM_NAMES = {
  'indicator'                         => "indicator",    # For submit
  'type'                              => "type",         # For submit
  'descriptor_id'                     => "descriptor_id", # For update

  'description'                       => "description",
  'share_level'                       => "share_level",
  'status'                            => "status",
  'privacy_type'                      => "privacy_type",
  'privacy_members'                   => "privacy_members",
  'tags'                              => "tags",
  'add_tags'                          => "add_tags",
  'remove_tags'                       => "remove_tags",
  'confidence'                        => "confidence",
  'precision'                         => "precision",
  'review_status'                     => "review_status",
  'severity'                          => "severity",
  'expired_on'                        => "expired_on",
  'first_active'                      => "first_active",
  'last_active'                       => "last_active",
  'related_ids_for_upload'            => "related_ids_for_upload",
  'related_triples_for_upload_as_json' => "related_triples_for_upload_as_json",
  # Legacy: should have been named reactions_to_add, but isn't. :(
  'reactions'                         => "reactions",
  'reactions_to_remove'               => "reactions_to_remove",
}

@@TE_BASE_URL = ThreatExchange::TENet::DEFAULT_TE_BASE_URL
@@APP_TOKEN = nil

# ----------------------------------------------------------------
# E.g. for overridiing
#   https://graph.facebook.com/v{i}.{j}
# to
#   https://graph.facebook.com/v{x}.{y}
def TENet.setTEBaseURL(baseURL)
  @@TE_BASE_URL = baseURL
end

# ----------------------------------------------------------------
# Gets the ThreatExchange app token from an environment variable.
# Feel free to replace the app-token discovery method here with whatever
# is most convenient for your project. However, be aware that app tokens
# are like passwords and shouldn't be stored in the open.

# I like to put export TX_ACCESS_TOKEN=$(cat ~/.txtoken) in my .bashrc
# where ~/.txtoken is a mode-600 file.

def TENet.setAppTokenFromEnvName(appTokenEnvName)
  value = ENV[appTokenEnvName]
  if value.nil?
    raise "ThreatExchange::TENet::setAppToken: \"#{appTokenEnvName}\" not in ENV."
  end
  @@APP_TOKEN = value
end

# ----------------------------------------------------------------
# Looks up the "objective tag" ID for a given tag. This is suitable input for the /threat_tags endpoint.

def TENet.getTagIDFromName(tagName, showURLs: false)
  url = @@TE_BASE_URL +
      "/threat_tags" +
      "/?access_token=" + CGI::escape(@@APP_TOKEN) +
      "&text=" + CGI::escape(tagName)

  if showURLs
    puts "URL:"
    puts url
  end

  noMatchFoundString = "ThreatExchange::TENet::getTagIDFromName: did not find \"#{tagName}\""
  protocolErrorString = "ThreatExchange::TENet::getTagIDFromName: protocol error finding \"#{tagName}\""

  responseString = Net::HTTP.get(URI(url))
  responseObject = JSON.parse(responseString)

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

  dataObject = responseObject['data']
  if dataObject.nil?
    raise protocolErrorString
  end
  matches = dataObject.select{|item| item['text'] == tagName}
  if matches.length != 1
    raise noMatchFoundString
  end

  id = matches[0]['id']
  if id.nil?
    raise protocolErrorString
  end
  return id
end

# ----------------------------------------------------------------
# Looks up all descriptors with a given tag. Invokes a specified callback on
# each page of IDs.

def TENet.processDescriptorIDsByTagID(
  tagID,    # string
  verbose: false,  # boolean
  showURLs: false, # verbose
  taggedSince: nil,   # nullable string
  taggedUntil: nil,   # nullable string
  pageSize: 10, # int
  includeIndicatorInOutput: true,
  idProcessor: nil)# IDProcessor callback-class instance

  startURL = @@TE_BASE_URL +
    "/" + tagID + "/tagged_objects" +
    "/?access_token=" + CGI::escape(@@APP_TOKEN) +
    "&limit=" + pageSize.to_s
  unless taggedSince.nil?
    startURL += "&tagged_since=" + CGI::escape(taggedSince)
  end
  unless taggedUntil.nil?
    startURL += "&tagged_until=" + CGI::escape(taggedUntil)
  end

  nextURL = startURL
  pageIndex = 0;

  loop do
    if showURLs
      puts "URL:"
      puts nextURL
    end

    protocolErrorString = "ThreatExchange::TENet::getDescriptorIDsByTagID: protocol error finding descriptors for tag ID \"#{tagID}\""

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

    responseString = Net::HTTP.get(URI(nextURL))
    responseObject = JSON.parse(responseString)

    dataObject = responseObject['data']
    if dataObject.nil?
      $stderr.puts(responseObject)
      raise protocolErrorString
    end
    pagingObject = responseObject['paging']
    if pagingObject.nil?
      nextURL = nil
    else
      nextURL = pagingObject['next']
    end

    ids = []
    dataObject.each do |item|
      itemID = item['id']
      itemType = item['type']
      if includeIndicatorInOutput
        itemName = item['name']
      else
        item.delete('name')
      end

      if itemType != ThreatExchange::TENet::THREAT_DESCRIPTOR
        next
      end

      if verbose
        puts item.to_json
      end

      ids.push(itemID)
    end

    if verbose
      info = {}
      info['page_index'] = pageIndex
      info['num_items_pre_filter'] = dataObject.length
      info['num_items_post_filter'] = ids.length
      puts info.to_json
    end

    idProcessor.call(ids)

    pageIndex += 1

    break if nextURL.nil?
  end # loop
end

# ----------------------------------------------------------------
# Looks up all metadata for given IDs.
def TENet.getInfoForIDs(
  ids, # list of string
  verbose: false, # boolean,
  showURLs: false, # boolean,
  includeIndicatorInOutput: true) # boolean

  # Check well-formattedness of descriptor IDs (which may have come from
  # arbitrary data on stdin).
  ids.each do |id|
    begin
      intValue = Integer(id)
    rescue ArgumentError
      raise "Malformed descriptor ID \"#{id}\""
    end
  end

  # See also
  # https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-descriptor/v6.0
  # for available fields

  startURL = @@TE_BASE_URL +
    "/?access_token=" + CGI::escape(@@APP_TOKEN) +
    "&ids=" + CGI::escape(ids.join(',')) +
    "&fields=raw_indicator,type,added_on,last_updated,confidence,owner,privacy_type,review_status,status,severity,share_level,tags,description,reactions,my_reactions"

  if showURLs
    puts "URL:"
    puts startURL
  end

  protocolErrorString = "ThreatExchange::TENet::getInfoForIDs: protocol error finding IDs \"#{ids.join(',')}\""

  # Example response:
  #
  # {
  #    "990927953l366387": {
  #       "raw_indicator": "87f4b261064696075fffceee39471952",
  #       "type": "HASH_MD5",
  #       "added_on": "2018-03-21T18:47:23+0000",
  #       "confidence": 100,
  #       "owner": {
  #          "id": "788842735455502",
  #          "email": "contactemail\u0040companyname.com",
  #          "name": "Name of App"
  #       },
  #       "review_status": "REVIEWED_AUTOMATICALLY",
  #       "severity": "WARNING",
  #       "share_level": "AMBER",
  #       "tags": {
  #          "data": [
  #             {
  #                "id": "8995447960580728",
  #                "text": "media_type_video"
  #             },
  #             {
  #                "id": "6000177b99449380",
  #                "text": "media_priority_test"
  #             }
  #          ]
  #       },
  #       "id": "4019972332766623"
  #    },
  #    ...
  #  }

  responseString = Net::HTTP.get(URI(startURL))
  if responseString.nil?
    raise protocolErrorString
  end
  responseObject = JSON.parse(responseString)
  if responseObject.nil?
    raise protocolErrorString
  end

  descriptors = []
  responseObject.each do |id, descriptor|
    if includeIndicatorInOutput == false
      descriptor.delete('raw_indicator')
    end

    if verbose
      puts descriptor.to_json
    end

    tags = descriptor['tags']
    if tags.nil?
      tags = []
    else
      tags = tags['data']
    end

    # Canonicalize the tag ordering and simplify the structure to simply an
    # array of tag-texts
    descriptor['tags'] = tags.map{|tag| tag['text']}.sort

    if descriptor['description'].nil?
      descriptor['description'] = ""
    end

    descriptors.push(descriptor)
  end

  return descriptors
end

# ----------------------------------------------------------------
# Returns error message or nil.
# This simply checks to see (client-side) if required fields aren't provided.
def TENet.validatePostPararmsForSubmit(postParams)
  unless postParams[POST_PARAM_NAMES[:descriptor_id]].nil?
    return "descriptor_id must not be specified for submit."
  end

  requiredFields = [
    POST_PARAM_NAMES[:indicator],
    POST_PARAM_NAMES[:type],
    POST_PARAM_NAMES[:description],
    POST_PARAM_NAMES[:share_level],
    POST_PARAM_NAMES[:status],
    POST_PARAM_NAMES[:privacy_type],
  ]

  missingFields = requiredFields.map do |fieldName|
    postParams[fieldName].nil? ? fieldName : nil
  end
  missingFields = missingFields.select do |fieldName|
    fieldName != nil
  end

  if missingFields.length == 0
    return nil
  elsif missingFields.length == 1
    return "Missing field #{missingFields[0]}."
  else
    return "Missing fields #{missingFields.join(', ')}."
  end
end

# ----------------------------------------------------------------
# Returns error message or nil.
# This simply checks to see (client-side) if required fields aren't provided.
def TENet.validatePostPararmsForUpdate(postParams)
  if postParams[POST_PARAM_NAMES[:descriptor_id]].nil?
    return "Descriptor ID must be specified for update."
  end
  unless postParams[POST_PARAM_NAMES[:indicator]].nil?
    return "indicator must not be specified for update."
  end
  unless postParams[POST_PARAM_NAMES[:type]].nil?
    return "type must not be specified for update."
  end
  return nil
end

# ----------------------------------------------------------------
# Returns error message or nil.
# This simply checks to see (client-side) if required fields aren't provided.
def TENet.validatePostPararmsForCopy(postParams)
  if postParams[POST_PARAM_NAMES[:descriptor_id]].nil?
    return "Source-descriptor ID must be specified for copy."
  end
  if postParams[POST_PARAM_NAMES[:privacy_type]].nil?
    return "Privacy type must be specified for copy."
  end
  if postParams[POST_PARAM_NAMES[:privacy_members]].nil?
    return "Privacy type must be specified for copy."
  end
  return nil
end

# ----------------------------------------------------------------
# Does a single POST to the threat_descriptors endpoint.  See also
# https://developers.facebook.com/docs/threat-exchange/reference/submitting
def TENet.submitThreatDescriptor(
  postParams,
  showURLs: false, # boolean,
  dryRun: false) # boolean,

  errorMessage = ThreatExchange::TENet.validatePostPararmsForSubmit(postParams)
  unless errorMessage.nil?
    return [errorMessage, nil, nil]
  end

  urlString = @@TE_BASE_URL +
    "/threat_descriptors" +
    "/?access_token=" + CGI::escape(@@APP_TOKEN)

  return TENet._postThreatDescriptor(
    urlString,
    postParams,
    showURLs: showURLs,
    dryRun: dryRun
  )
end

# ----------------------------------------------------------------
# Does a single POST to the threat_descriptor ID endpoint.  See also
# https://developers.facebook.com/docs/threat-exchange/reference/editing
def TENet.updateThreatDescriptor(
  postParams,
  showURLs: false, # boolean,
  dryRun: false) # boolean,

  errorMessage = ThreatExchange::TENet.validatePostPararmsForUpdate(postParams)
  unless errorMessage.nil?
    return [errorMessage, nil, nil]
  end

  urlString = @@TE_BASE_URL +
    "/" + postParams[POST_PARAM_NAMES[:descriptor_id]] +
    "/?access_token=" + CGI::escape(@@APP_TOKEN)

  return TENet._postThreatDescriptor(
    urlString,
    postParams,
    showURLs: showURLs,
    dryRun: dryRun
  )
end

# ----------------------------------------------------------------
def TENet.copyThreatDescriptor(
  postParams,
  showURLs: false, # boolean,
  dryRun: false) # boolean,

  errorMessage = ThreatExchange::TENet.validatePostPararmsForCopy(postParams)
  unless errorMessage.nil?
    return [errorMessage, nil, nil]
  end

  # Get source descriptor
  sourceID = postParams[POST_PARAM_NAMES[:descriptor_id]]
  postParams.delete(POST_PARAM_NAMES[:descriptor_id])
  sourceDescriptor = TENet.getInfoForIDs([sourceID], showURLs:showURLs)
  sourceDescriptor = sourceDescriptor[0]

  # Mutate necessary fields
  newDescriptor = Marshal.load(Marshal.dump(sourceDescriptor)) # deepcopy
  newDescriptor['indicator'] = sourceDescriptor['raw_indicator']
  newDescriptor.delete('raw_indicator')
  if newDescriptor['tags'] != nil
    newDescriptor.delete('tags')
  end

  # The shape is different between the copy-from data (mapping app IDs to
  # reactions) and the post data (just a comma-delimited string of owner-app
  # reactions).
  if newDescriptor['reactions'] != nil
    newDescriptor.delete('reactions')
  end

  # Take the source-descriptor values and overwrite any post-params fields
  # supplied by the caller. Note: Ruby's hash-merge method keeps the old
  # value for a given field name when both old and new are present so we
  # invoke it seemingly 'backward'.
  #
  # Example:
  # * x = {'a' => 1, 'b' => 2, 'c' => 3}
  # * y = {'a' => 1, 'b' => 9, 'd' => 12}
  # * z = y.merge(x)
  # * z = {"a"=>1, "b"=>2, "d"=>12, "c"=>3}
  #
  # This means we want newDescriptor.merge(postParams)
  newDescriptor = newDescriptor.merge(postParams)

  # Get rid of fields like last_upated from the source descriptor which
  # aren't valid for post
  postParams = {}
  newDescriptor.each do |key, value|
    if STRING_POST_PARAM_NAMES[key] != nil
      postParams[key] = value
    end
  end

  return self.submitThreatDescriptor(postParams, showURLs:showURLs, dryRun:dryRun)
end


# ----------------------------------------------------------------
# Code-reuse for submit and update
def TENet._postThreatDescriptor(
  urlString,
  postParams,
  showURLs: false, # boolean,
  dryRun: false) # boolean,


  postParams.each do |key, value|
    urlString += "&#{key}=" + CGI::escape(value.to_s)
  end

  if showURLs
    puts
    puts "URL:"
    puts urlString
  end

  if (dryRun)
    puts "Not doing POST since --dry-run."
    return [nil, '', nil]
  else
    header = {
      'Content-Type' =>  'text/json',
      'charset' => 'utf-8',
    }
    uri = URI.parse(urlString)
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = true
    request = Net::HTTP::Post.new(uri.request_uri, header)
    request.body = postParams.to_json

    response = http.request(request)

    return [nil, response.body, response.code]
  end

end # TENet.submitThreatDescriptor

# ----------------------------------------------------------------
# This is for client-side creation-time filtering. We accept the same
# command-line values as for tagged-time filtering which is done server-side
# using PHP\strtotime which takes various epoch-seconds timestamps, various
# format strings, and time-deltas like "-3hours" and "-1week".  Here we
# re-invent some of PHP\strtotime.
def TENet.parseTimeStringToEpochSeconds(mixedString)
  retval = TENet._parseIntStringToEpochSeconds(mixedString)
  return retval unless retval.nil?

  retval = TENet._parseDateTimeStringToEpochSeconds(mixedString)
  return retval unless retval.nil?

  retval = TENet._parseRelativeStringToEpochSeconds(mixedString)
  return retval unless retval.nil?
  return nil
end # TENet.parseTimeStringToEpochSeconds

# Helper for parseTimeStringToEpochSeconds to try epoch-seconds timestamps
def TENet._parseIntStringToEpochSeconds(mixedString)
  begin
    return Integer(mixedString)
  rescue ArgumentError
    return nil
  end
end

DATETIME_FORMATS = [
  '%Y-%m-%dT%H:%M:%S%z', # TE server-side date format -- try first
  '%Y-%m-%d %H:%M:%S',
  '%Y/%m/%d %H:%M:%S',
  '%Y-%m-%dT%H:%M:%S',
  '%Y-%m-%dT%H:%M:%SZ',
]

# Helper for parseTimeStringToEpochSeconds to try various format-string
# timestamps
def TENet._parseDateTimeStringToEpochSeconds(mixedString)
  DATETIME_FORMATS.each do |formatString|
    begin
      return DateTime.strptime(mixedString, formatString).to_time.to_i
    rescue ArgumentError
      return nil
    end
  end
   return nil
 end

# Helper for parseTimeStringToEpochSeconds to try various relative-time
# indications.
def TENet._parseRelativeStringToEpochSeconds(mixedString)
  retval = TENet._parseRelativeStringMinute(mixedString)
  return retval unless retval.nil?
  retval = TENet._parseRelativeStringHour(mixedString)
  return retval unless retval.nil?
  retval = TENet._parseRelativeStringDay(mixedString)
  return retval unless retval.nil?
  retval = TENet._parseRelativeStringWeek(mixedString)
  return retval unless retval.nil?
  return nil
end

# Helper for parseTimeStringToEpochSeconds to try particular relative-time
# indications.
def TENet._parseRelativeStringMinute(mixedString)
  output = mixedString.match("^-([0-9]+)minutes?$")
  if output != nil
    count = Integer(output[1])
    return DateTime.now.to_time.to_i - count * 60 # timezone-unsafe
  else
    return nil
  end
end

# Helper for parseTimeStringToEpochSeconds to try particular relative-time
# indications.
def TENet._parseRelativeStringHour(mixedString)
  output = mixedString.match("^-([0-9]+)hours?$")
  if output != nil
    count = Integer(output[1])
    return DateTime.now.to_time.to_i - count * 60 * 60 # timezone-unsafe
  else
    return nil
  end
end

# Helper for parseTimeStringToEpochSeconds to try particular relative-time
# indications.
def TENet._parseRelativeStringDay(mixedString)
  output = mixedString.match("^-([0-9]+)days?$")
  if output != nil
    count = Integer(output[1])
    return DateTime.now.to_time.to_i - count * 24 * 60 * 60 # timezone-unsafe
  else
    return nil
  end
end

# Helper for parseTimeStringToEpochSeconds to try particular relative-time
# indications.
def TENet._parseRelativeStringWeek(mixedString)
  output = mixedString.match("^-([0-9]+)weeks?$")
  if output != nil
    count = Integer(output[1])
    return DateTime.now.to_time.to_i - count * 7 * 24 * 60 * 60 # timezone-unsafe
  else
    return nil
  end
end

end # module TENet
end # module ThreatExchange

# ================================================================
# Validator for client-side creation-time datetime parsing. Not written as unit
# tests per se since "-1week" et al. are dynamic things. Invoke via "ruby TENet.rb".
if __FILE__ == $0
  def showParseTimeStringToEpochSeconds(mixedString)
    retval = ThreatExchange::TENet::parseTimeStringToEpochSeconds(mixedString)
    readable = 'nil'
    if retval != nil
      readable = Time.at(retval).to_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')
    end
    puts("#{mixedString.ljust(30)} #{retval.to_s.ljust(30)} #{readable}")
  end

  showParseTimeStringToEpochSeconds("1591626448")
  showParseTimeStringToEpochSeconds("2020-06-08T14:27:53Z")
  showParseTimeStringToEpochSeconds("2020-06-08T14:27:53+0400")
  showParseTimeStringToEpochSeconds("2020-06-08T14:27:53-0400")
  showParseTimeStringToEpochSeconds("2020-05-01T07:02:25+0000")
  showParseTimeStringToEpochSeconds("-1minute")
  showParseTimeStringToEpochSeconds("-3minutes")
  showParseTimeStringToEpochSeconds("-1hour")
  showParseTimeStringToEpochSeconds("-3hours")
  showParseTimeStringToEpochSeconds("-1day")
  showParseTimeStringToEpochSeconds("-3day")
  showParseTimeStringToEpochSeconds("-1week")
  showParseTimeStringToEpochSeconds("-3weeks")
  showParseTimeStringToEpochSeconds("nonesuch")
end
