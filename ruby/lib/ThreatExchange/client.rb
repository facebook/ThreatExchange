# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
require "ThreatExchange/http_methods"
require "logger"

module ThreatExchange
  # The ThreatExchange::Client object handles all interactions
  # with https://graph.facebook.com.
  # Some TODO's - Better Error handling and explicit requirements
  # around parameters passed to the methods.
  #
  # Docs: https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-exchange-members/v2.6
  #
  class Client
    include HttpMethods

    attr_accessor :app_id

    def initialize(app_id, secret, version: 'v2.6', logfile: STDOUT)
      @app_id = app_id
      @secret = secret
      @access_token = "#{@app_id}|#{@secret}"
      @baseurl = 'https://graph.facebook.com'
      @version = version
      @logger = ::Logger.new(logfile)
    end

    # Optional:
    #   sample_type - Defines the type of malware, one of MalwareAnalysisType
    #   share_level - A given value of ShareLevelType
    #   text - Freeform text field with a value to search for. This can be a file hash or a string found in other fields of the objects.
    #   status - A given StatusType
    #   strict_text - When set to 'true', the API will not do approximate matching on the value in text
    def malware_analyses(params={})
      result = get "malware_analyses", params

      data = result['data']
      cursor = result.fetch('paging', {}).fetch('cursor', {}).fetch('after', nil)

      until cursor.nil?
        result = get "malware_analyses", (params || {}).merge(after: cursor)
        if result['data'].empty?
          cursor = nil
        else
          result['data'].each { |r| data <<  r }
          cursor = result.fetch('paging', {}).fetch('cursor', {}).fetch('after', nil)
        end
      end

      data
    end

    # Optional:
    #   text - Freeform text field with a value to search for. This can be a file hash or a string found in other fields of the objects.
    #   strict_text - When set to 'true', the API will not do approximate matching on the value in text
    def malware_families(params={})
      result = get "malware_families", params
    end

    # Optional:
    #   strict_text - When set to 'true', the API will not do approximate matching on the value in text
    #   threat_type - The broad threat type the indicator is associated with (see ThreatTypes)
    #   type - The type of indicators to search for (see IndicatorTypes)
    def threat_indicators(params={})
      result = get "threat_indicators", params

      data = result['data']

      return data if params[:limit] && data.size >= params[:limit]

      while cursor = result.fetch('paging', {}).fetch('cursors', {}).fetch('after', nil)
        result = get "threat_indicators", (params || {}).merge(after: cursor)
        if result['data'].empty?
          cursor = nil
        else
          result['data'].each do |r|
            data << r
            return data if params[:limit] && data.size >= params[:limit]
          end
          cursor = result.fetch('paging', {}).fetch('cursors', {}).fetch('after', nil)
        end
      end
      return data
    end

    # Optional:
    #   include_expired - When set to true, the API can return data which has expired. Expired data is denoted by having the expire_time field as non-zero and less than the current time.
    #   attack_type - A given AttackType
    #   max_confidence - Define the maximum allowed confidence value for the data returned.
    #   min_confidence - Define the minimum allowed confidence value for the data returned.
    #   owner - Comma separated list of app_ids of the person who submitted the data.
    #   text - Freeform text field with a value to search for. This can be a file hash or a string found in other fields of the objects.
    #   review_status - A given ReviewStatusType
    #   share_level - A given ShareLevelType
    #   status - A given StatusType
    #   strict_text - When set to 'true', the API will not do approximate matching on the value in text
    #   threat_type - The broad threat type the descriptor is associated with (see ThreatTypes)
    #   type - The type of descriptor to search for (see IndicatorTypes)
    def threat_descriptors(params={})
      get "threat_descriptors", params
    end

    # Required:
    #  id - the id of the Indicator
    def get_indicator(params={})
      assert_params(params, :id)
      id = (params || {})[:id]

      get "#{id}/", params
    end

    def members(params={})
      get "threat_exchange_members/", params
    end

    # Required:
    #   name - The name of the threat privacy group.
    #   description - A human readable description of the group.
    # Optional:
    #   members - A list of ThreatExchangeMembers to be added to the group. Can be modified later.
    #   members_can_see - If true, group members can view this group, including its name, description, and list of members. Defaults to FALSE.
    #   members_can_use - If true, members are allowed to use this group to protect their own threat data. Defaults to FALSE.
    #   fields - A list of fields to return in the response
    def new_threat_privacy_group(params={})
      assert_params(params, :name, :description)

      post "threat_privacy_groups/", params
    end

    # Optional:
    #   name - Allows filtering by privacy group name
    #   description - Allows filtering by privacy group description
    def owned_threat_privacy_groups(params={})
      get "/#{@app_id}/threat_privacy_groups_owner", params
    end

    # Optional:
    #   name - Allows filtering by privacy group name
    #   description - Allows filtering by privacy group description
    def member_threat_privacy_groups(params={})
      get "/#{@app_id}/threat_privacy_groups_member", params
    end

    # Required:
    #   id - a FB object
    #   related_id - another object from which to establish an association
    def new_relation(params={})
      assert_params(params, :id, :related_id)
      id = (params || {})[:id]

      post "#{id}/related", params
    end

    # Required:
    #   id - id of the Relation
    def remove_relation(params={})
      assert_params(params, :id, :related_id)
      id = (params || {})[:id]

      delete "#{id}/related/", params
    end

    # Required:
    #   description - A short summary of the indicator and threat;
    #   indicator - The indicator data being submitted;
    #   privacy_type - The kind of privacy for the indicator, see PrivacyType for the list of allowed values;
    #   share_level - A designation of how the indicator may be shared based on the US-CERT's Traffic Light Protocol, see ShareLevelType for the list of allowed values;
    #   status - Indicates if the indicator is labeled as malicious;
    #   type - The kind of indicator being described, see IndicatorType for the list of allowed values.
    # Optional:
    #   confidence - A score for how likely the indicator's status is accurate, ranges from 0 to 100;
    #   expired_on - Time the indicator is no longer considered a threat, in ISO 8601 date format;
    #   precision - The degree of accuracy of the indicator, see PrecisionType for the list of allowed values;
    #   privacy_members - A comma-delimited list of ThreatExchangeMembers allowed to see the indicator and only applies when privacy_type is set to HAS_WHITELIST;
    #   review_status - Describes how the indicator was vetted, see ReviewStatusType for the list of allowed values;
    #   severity - A rating of how severe the indicator is when found in an incident, see SeverityType for the list of allowed values;
    #   threat_type - The broad threat type the indicator is associated with, see ThreatType for the list of allowed values;
    def new_descriptor(params={})
      assert_params(params, :description, :indicator, :privacy_type, :share_level, :status, :type)

      post "threat_descriptors", params
    end

    # See https://developers.facebook.com/docs/threat-exchange/reference/submitting/v2.4
    def new_ioc(params={})
      raise "Error: v2.4 replaced 'POST /threat_indicators' with 'POST /threat_descriptors'"
    end

    def update_ioc(params={})
      @logger.info "Warning: 'update_ioc' was deprecated and renamed to 'update_indicator'"
      update_indicator(params)
    end

    # Required:
    #   id - id of the Indicator
    def update_indicator(params={})
      assert_params(params, :id)
      id = (params || {})[:id]

      result = post "#{id}", params.merge(access_token: @access_token)
    end


    private def assert_params(params, *required_params)
      missing_params = required_params - params.keys

      if missing_params.size > 0
        raise ArgumentError.new("Missing required params: #{missing_params.join(',')}")
      end
    end
  end
end
