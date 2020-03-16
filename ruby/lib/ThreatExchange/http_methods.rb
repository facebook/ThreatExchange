# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
require "rest-client"

module ThreatExchange
  class Client
    module HttpMethods
      # Common GET Options:
      #   limit - Defines the maximum size of a page of results. The maximum is 1,000.
      #   since - Returns malware collected after a timestamp
      #   until - Returns malware collected before a timestamp
      #   fields - A list of fields to return in the response
      #   sort_order - A given SortOrderType
      private def get(path, params={})
        response = RestClient.get "#{@baseurl}/#{@version}/#{path}", params: (params || {}).merge(access_token: @access_token)
        JSON.parse(response)
      rescue => e
        puts e.inspect
      end

      private def post(path, body={})
        response = RestClient.post "#{@baseurl}/#{@version}/#{path}", (body || {}).merge(access_token: @access_token)
        JSON.parse(response)
      rescue => e
        puts e.inspect
      end

      private def delete(path, params={})
        response = RestClient.delete "#{@baseurl}/#{@version}/#{path}", params: (params || {}).merge(access_token: @access_token)
        JSON.parse(response)
      rescue => e
        puts e.inspect
      end
    end
  end
end
