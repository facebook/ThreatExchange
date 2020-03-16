# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
require 'test_helper'

describe "client" do
  before(:all) do
  end

  describe ".new" do
    it "sets app_id" do
      client = ThreatExchange::Client.new(1, 'secret')
      value(client.app_id).must_equal 1
    end
  end

  describe "#malware_analyses" do
    it "gets paged data" do
      response = {
        "data": [
          {
            "added_on": "2014-02-08T10:45:08+0000",
            "md5": "f5c3281ed489772c840a137011c76b58",
            "sha1": "2517620f427f0019e2eee3b36e206567b6e7a74a",
            "sha256": "cb57e263ab51f8e9b40d6f292bb17512cec0aa701bde14df33dfc06c815be54c",
            "status": "UNKNOWN",
            "victim_count": 0,
            "id": "760220740669930"
          },
        ],
        "paging": {
          "cursors": {
          },
          "next": "https://graph.facebook.com/v2.8/malware_analyses?access_token=5555|1234&pretty=0&since=1391813489&until=1391856689&limit=25&after=MjQZD"
        },
      }.to_json

      stub_request(:get, /malware_analyses/).
        to_return(:status => 200, :body => response)

      client = ThreatExchange::Client.new(1, 'secret')
      data = client.malware_analyses

      value(data).must_equal([{"added_on"=>"2014-02-08T10:45:08+0000",
                               "md5"=>"f5c3281ed489772c840a137011c76b58",
                               "sha1"=>"2517620f427f0019e2eee3b36e206567b6e7a74a",
                               "sha256"=>"cb57e263ab51f8e9b40d6f292bb17512cec0aa701bde14df33dfc06c815be54c",
                               "status"=>"UNKNOWN",
                               "victim_count"=>0,
                               "id"=>"760220740669930"}])
    end
  end

  describe "#members" do
    it "gets data" do
      response = {
        "data": [
          {
            "id": "820763734618599",
            "email": "threatexchange@support.facebook.com",
            "name": "Facebook ThreatExchange"
          } ] }.to_json

          stub_request(:get, /threat_exchange_members/).
            to_return(:status => 200, :body => response)

          client = ThreatExchange::Client.new(1, 'secret')
          data = client.members

          value(data).must_equal({"data"=>[
            {"id"=>"820763734618599",
             "email"=>"threatexchange@support.facebook.com",
             "name"=>"Facebook ThreatExchange"}]})
    end
  end
end

