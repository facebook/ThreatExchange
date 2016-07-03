require "ThreatExchange/version"
require "rest-client"
require "json"
require 'logger'
module ThreatExchange

  # The ThreatExchange::Client object handles all interactions
  # with https://graph.facebook.com.
  # Some TODO's - Better Error handling and explicit requirements
  # around parameters passed to the methods.
  #
  class Client

    attr_accessor :access_token

    def initialize(access_token = nil, logfile = STDOUT)
      @access_token = access_token
      @baseurl = 'https://graph.facebook.com'
      @logger = Logger.new(logfile)
    end

    def malware_analyses(params = {})
      result = get("#{@baseurl}/malware_analyses", params)
      data = result['data']
      cursor = result.fetch('paging', {}).fetch('cursor', {}).fetch('after', nil)

      until cursor.nil?
        result = get("#{@baseurl}/malware_analyses", params.merge(after: cursor))
        if result['data'].empty?
          cursor = nil
        else
          result['data'].each { |r| data <<  r }
          cursor = result.fetch('paging', {}).fetch('cursor', {}).fetch('after', nil)
        end
      end

      data
    end

    def threat_indicators(params = {})
      result = get("#{@baseurl}/threat_indicators", params)

      data = result['data']

      while cursor = result.fetch('paging', {}).fetch('cursors', {}).fetch('after', nil)
        params_with_cursor = (params || {}).merge(after: cursor)
        result = get("#{@baseurl}/threat_indicators", params_with_cursor)
        if result['data'].empty?
          cursor = nil
        else
          result['data'].each { |r| data <<  r }
          cursor = result.fetch('paging', {}).fetch('cursors', {}).fetch('after', nil)
        end
      end

      data
    end

    def indicator_pq(params = {})
      get("#{@baseurl}/#{params[:id]}/", params)
    end

    def members(params = {})
      get("#{@baseurl}/threat_exchange_members/", params)
    end

    def new_relation(params = {})
      post("#{@baseurl}/#{params[:id]}/related", params)
    end

    def remove_relation(params = {})
      delete("#{@baseurl}/#{params[:id]}/related/", params)
    end

    def new_ioc(params = {})
      if params.has_key?(:privacy_type)
        post("#{@baseurl}/threat_indicators", params)
      else
        raise ArgumentError.new("You must set a privacy_type in your query")
      end
    end

    def update_ioc(params = {})
      result = post("#{@baseurl}/#{params[:id]}", params.merge(access_token: @access_token))
    end

    ##
    ## Request Methods
    ##
    private def get(url, params = {})
      params_with_access_token = (params || {}).merge(access_token: @access_token)
      response = RestClient.get(url, params: params_with_access_token)
      JSON.parse(response)
    rescue => e
      @logger.info e.inspect
    end

    private def post(url, body = {})
      body_with_access_token = (body || {}).merge(access_token: @access_token)
      response = RestClient.post(url, body: body_with_access_token)
      JSON.parse(response)
    rescue => e
      @logger.info e.inspect
    end

    private def delete(url, params = {})
      params_with_access_token = (params || {}).merge(access_token: @access_token)
      response = RestClient.delete(url, params: params_with_access_token)
      JSON.parse(response)
    rescue => e
      @logger.info e.inspect
    end
  end
end
