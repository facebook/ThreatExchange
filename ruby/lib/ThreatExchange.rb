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

    def malware_analyses(filter={})
      filter[:access_token] = @access_token
      begin
        response = RestClient.get "#{@baseurl}/malware_analyses",
        { params: filter  }
        result = JSON.parse(response)
      rescue => e
        puts e.inspect
      end
      data = result['data']
      cursor = result.fetch('paging', {}).fetch('cursor', {}).fetch('after', nil)

      until cursor.nil?
        filter[:after] = cursor
        begin
          response = RestClient.get "#{@baseurl}/malware_analyses",
          { params: filter }
          result = JSON.parse(response)
        rescue => e
          puts e.inspect
        end
        if result['data'].empty?
          cursor = nil
        else
          result['data'].each { |r| data <<  r }
          cursor = result.fetch('paging', {}).fetch('cursor', {}).fetch('after', nil)
        end
      end
      return data
    end

    def threat_indicators(filter={})
      filter[:access_token] = @access_token
      begin
        response = RestClient.get "#{@baseurl}/threat_indicators",
        { params: filter }
        result = JSON.parse(response)
      rescue => e
        puts e.inspect
      end
      data = result['data']

      while cursor = result.fetch('paging', {}).fetch('cursors', {}).fetch('after', nil)
        filter[:after] = cursor
        begin
          response = RestClient.get "#{@baseurl}/threat_indicators",
          { params: filter }
          result = JSON.parse(response)
        rescue => e
          puts e.inspect
        end
        if result['data'].empty?
          cursor = nil
        else
          result['data'].each { |r| data <<  r }
          cursor = result.fetch('paging', {}).fetch('cursors', {}).fetch('after', nil)
        end
      end
      return data
    end

    def indicator_pq(filter={})
      begin
        response = RestClient.get "#{@baseurl}/#{filter[:id]}/",
        { params: { access_token: @access_token, fields: filter[:fields] } }
        result = JSON.parse(response)
        return result
      rescue => e
        puts e.inspect
      end
    end

    def members()
      begin
        response = RestClient.get "#{@baseurl}/threat_exchange_members/",
        { params: { access_token: @access_token } }
        result = JSON.parse(response)
        return result['data']
      rescue => e
        e.response
      end
    end

    def new_relation(data={})
      data[:access_token] = @access_token
      id = data.delete(:id)
      begin
        response = RestClient.post "#{@baseurl}/#{id}/related", data
      rescue => e
        e.inspect
      end
    end

    def remove_relation(data={})
      data[:access_token] = @access_token
      id = data.delete(:id)
      begin
        response = RestClient.delete "#{@baseurl}/#{id}/related/",
        { params: data }
      rescue => e
        e.response
      end
    end

    def new_ioc(data={})
      data[:access_token] = @access_token
      if data.has_key?(:privacy_type)
        begin
          response = RestClient.post "#{@baseurl}/threat_indicators", data
          return response
        rescue => e
          e.inspect
        end
      else
        puts "You must set a privacy_type in your query"
      end
    end

    def update_ioc(data={})
      data[:access_token] = @access_token
      id = data.delete(:id)
      begin
        response = RestClient.post "#{@baseurl}/#{id}", data
      rescue => e
        e.inspect
      end
    end

  end
end
