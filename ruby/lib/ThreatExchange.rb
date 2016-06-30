require "ThreatExchange/version"
require "rest-client"
require "json"
module ThreatExchange

  # The ThreatExchange::Client object handles all interactions
  # with https://graph.facebook.com.
  # Some TODO's - Better Error handling and explicit requirements
  # around parameters passed to the methods.
  #
  class Client

    attr_accessor :access_token

    def initialize(access_token=nil)
      @access_token = access_token
      @baseurl = 'https://graph.facebook.com'
    end

    def malware_analyses(params={})
      params = params.merge(access_token: @access_token)

      result = get "#{@baseurl}/malware_analyses", params
      data = result['data']
      cursor = result.fetch('paging', {}).fetch('cursor', {}).fetch('after', nil)

      until cursor.nil?
        params[:after] = cursor
        result = get "#{@baseurl}/malware_analyses", params
        if result['data'].empty?
          cursor = nil
        else
          result['data'].each { |r| data <<  r }
          cursor = result.fetch('paging', {}).fetch('cursor', {}).fetch('after', nil)
        end
      end
      return data
    end

    def threat_indicators(params={})
      params = params.merge(access_token: @access_token)

      result = get "#{@baseurl}/threat_indicators", params

      data = result['data']

      while cursor = result.fetch('paging', {}).fetch('cursors', {}).fetch('after', nil)
        params[:after] = cursor
        result = get "#{@baseurl}/threat_indicators",
        if result['data'].empty?
          cursor = nil
        else
          result['data'].each { |r| data <<  r }
          cursor = result.fetch('paging', {}).fetch('cursors', {}).fetch('after', nil)
        end
      end
      return data
    end

    def indicator_pq(params={})
      params = params.merge(access_token: @access_token)

      get "#{@baseurl}/#{params[:id]}/", params
    end

    def members(params={})
      params = params.merge(access_token: @access_token)

      get "#{@baseurl}/threat_exchange_members/", params
    end

    def new_relation(params={})
      params = params.merge(access_token: @access_token)
      id = params.delete(:id)

      post "#{@baseurl}/#{id}/related", params
    end

    def remove_relation(params={})
      params = params.merge(access_token: @access_token)
      id = params.delete(:id)

      delete "#{@baseurl}/#{id}/related/", params
    end

    def new_ioc(params={})
      params = params.merge(access_token: @access_token)

      if params.has_key?(:privacy_type)
        post "#{@baseurl}/threat_indicators", params
      else
        puts "You must set a privacy_type in your query"
      end
    end

    def update_ioc(params={})
      params = params.merge(access_token: @access_token)
      id = params.delete(:id)

      result = post "#{@baseurl}/#{id}", params
    end

    ##
    ## Request Methods
    ##
    private def get(url, params={})
      response = RestClient.get url, params: params
      JSON.parse(response)
    rescue => e
      puts e.inspect
    end

    private def post(url, body={})
      response = RestClient.post url, body: body
      JSON.parse(response)
    rescue => e
      puts e.inspect
    end

    private def delete(url, params={})
      response = RestClient.delete url, params: params
      JSON.parse(response)
    rescue => e
      puts e.inspect
    end
  end
end
