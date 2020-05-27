# ================================================================
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
# ================================================================

# General Ruby dependencies
require 'CGI' # for URL-encoding
require 'net/http'
require 'uri'
require 'json'

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
}
POST_PARAM_NAMES.default_proc = -> (h, k) { raise KeyError, "POST_PARAM_NAMES[#{k}] is not defined." }

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

def TENet.getTagIDFromName(tagName:, showURLs: false)
  url = @@TE_BASE_URL +
      "/threat_tags" +
      "/?access_token=" + @@APP_TOKEN +
      "&text=" + CGI.escape(tagName)

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
  tagID:,    # string
  verbose: false,  # boolean
  showURLs: false, # verbose
  taggedSince: nil,   # nullable string
  taggedUntil: nil,   # nullable string
  pageSize: 10, # int
  includeIndicatorInOutput: true,
  idProcessor:)# IDProcessor callback-class instance

  startURL = @@TE_BASE_URL +
    "/" + tagID + "/tagged_objects" +
    "/?access_token=" + @@APP_TOKEN +
    "&limit=" + pageSize.to_s
  unless taggedSince.nil?
    startURL += "&tagged_since=" + taggedSince
  end
  unless taggedUntil.nil?
    startURL += "&tagged_until=" + taggedUntil
  end

  nextURL = startURL
  pageIndex = 0;

  loop do
    if showURLs
      puts "URL:"
      puts nextURL
    end

    protocolErrorString = "ThreatExchange::TENet::getDescriptorIDsByTagID: protocol error finding \"#{tagID}\""

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

      ids.append(itemID)
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
  ids:, # list of string
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
    "/?access_token=" + @@APP_TOKEN +
    "&ids=" + CGI.escape(ids.join(',')) +
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
  responseObject = JSON.parse(responseString)

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

    descriptors.append(descriptor)
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
  missingFields = missingFields.filter do |fieldName|
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
# Does a single POST to the threat_descriptors endpoint.  See also
# https://developers.facebook.com/docs/threat-exchange/reference/submitting
def TENet.submitThreatDescriptor(
  postParams:,
  showURLs: false, # boolean,
  dryRun: false) # boolean,

  errorMessage = ThreatExchange::TENet.validatePostPararmsForSubmit(postParams)
  unless errorMessage.nil?
    return [errorMessage, nil, nil]
  end

  urlString = @@TE_BASE_URL +
    "/threat_descriptors" +
    "/?access_token=" + @@APP_TOKEN

  return TENet._postThreatDescriptor(
    urlString: urlString,
    postParams: postParams,
    showURLs: showURLs,
    dryRun: dryRun
  )
end

# ----------------------------------------------------------------
# Does a single POST to the threat_descriptor ID endpoint.  See also
# https://developers.facebook.com/docs/threat-exchange/reference/editing
def TENet.updateThreatDescriptor(
  postParams:,
  showURLs: false, # boolean,
  dryRun: false) # boolean,

  errorMessage = ThreatExchange::TENet.validatePostPararmsForUpdate(postParams)
  unless errorMessage.nil?
    return [errorMessage, nil, nil]
  end

  urlString = @@TE_BASE_URL +
    "/" + postParams[POST_PARAM_NAMES[:descriptor_id]] +
    "/?access_token=" + @@APP_TOKEN

  return TENet._postThreatDescriptor(
    urlString: urlString,
    postParams: postParams,
    showURLs: showURLs,
    dryRun: dryRun
  )
end

# ----------------------------------------------------------------
# Code-reuse for submit and update
def TENet._postThreatDescriptor(
  urlString:,
  postParams:,
  showURLs: false, # boolean,
  dryRun: false) # boolean,


  postParams.each do |key, value|
    urlString += "&#{key}=" + CGI.escape(value)
  end

  if showURLs
    puts
    puts "URL:"
    puts urlString
  end

  if (dryRun)
    puts "Not doing POST since --dry-run."
    return ['', 0]
  else
    header = {
      'Content-Type':  'text/json',
      'charset': 'utf-8',
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

end # module TENet
end # module ThreatExchange
