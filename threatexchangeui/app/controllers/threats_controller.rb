class ThreatsController < ApplicationController
	skip_load_and_authorize_resource

	def result
		if !current_user.app_id.blank? && !current_user.app_secret.blank?
			query = {indicator_type: params[:indicator_type], text_query: params[:text_query]}
			@threat_indicators = threat_indicators(query)
			@indicator_type = params[:indicator_type]

			if params[:indicator_type].downcase == "ip_address"
				@country_array = Array.new

				@threat_indicators.each do |threat_indicator|
					@country_array.push(Geocoder.search(threat_indicator["indicator"]).first.country.to_s)
				end

				data_table = GoogleVisualr::DataTable.new
				data_table.new_column('string', 'Country' )
				data_table.new_column('number', 'Indicators')
				data_table.add_rows(chart_data(@country_array))
				
		  		option   = { height: 360 }
				@chart = GoogleVisualr::Interactive::GeoChart.new(data_table, option)
			end
		else
			redirect_to profile_path, notice: "Your Facebook App ID and App Secret are required to query Facebook Threat Exchange."
		end
	end

	def show
		if !current_user.app_id.blank? && !current_user.app_secret.blank?
			query = {text_query: params[:id]}
			@threat_descriptors = threat_descriptor(query)
		else
			redirect_to profile_path, notice: "Your Facebook App ID and App Secret are required to query Facebook Threat Exchange."
		end
	end

	def new
	end

	def create	
		if !params[:threat][:indicator].blank? && !params[:threat][:description].blank? && !params[:threat][:status].blank? && !params[:threat][:share_level].blank? && !params[:threat][:privacy].blank?
			@submit = submit_threat_descriptor(params[:threat])

			redirect_to(home_path, notice: "Threat indicator created")
		else
			flash[:notice] = "Please provide complete information about the threat indicator"
			render 'new'
		end
	end

	def submit
		puts params.inspect
	end

	private
	def get_base_url
		baseurl = "https://graph.facebook.com/v2.5"

		return baseurl
	end

	def get_access_token
		access_token = current_user.app_id + "|" + current_user.app_secret
	end

	def threat_indicators(filter={})
		# Search for threat indicators

		baseurl = get_base_url
		access_token = get_access_token

		begin
			if filter[:text_query].present?
				response = RestClient.get URI.encode("#{baseurl}/threat_indicators?access_token=#{access_token}&type=#{filter[:indicator_type]}&text=#{filter[:text_query]}&limit=50")
			else
				response = RestClient.get URI.encode("#{baseurl}/threat_indicators?access_token=#{access_token}&type=#{filter[:indicator_type]}&limit=50")
			end
			
			result = JSON.parse(response)
			data = result["data"]

			return data
		rescue => e
			puts e.inspect
		end
	end

	def threat_descriptor(filter={})
		# Show threat description for a particular threat indicator

		baseurl = get_base_url
		access_token = get_access_token

		begin
			response = RestClient.get URI.encode("#{baseurl}/threat_descriptors?access_token=#{access_token}&text=#{filter[:text_query]}&fields=id,added_on,confidence,description,expired_on,indicator,last_updated,owner,precision,raw_indicator,review_status,severity,share_level,status,threat_type,type,privacy_type")

			result = JSON.parse(response)
			data = result["data"]

			return data
		rescue => e
			puts e.inspect
		end
	end

	def submit_threat_descriptor(filter={})
		baseurl = get_base_url
		access_token = get_access_token

		begin
			post_data = "indicator=#{filter[:indicator]}&type=#{filter[:indicator_type]}&threat_type=#{filter[:threat]}&status=#{filter[:status]}&description=#{filter[:description]}&confidence=#{filter[:confidence]}&severity=#{filter[:severity]}&privacy_type=#{filter[:privacy]}&share_level=#{filter[:share_level]}"

			response = RestClient.post URI.encode("#{baseurl}/threat_descriptors?access_token=#{access_token}"), post_data

			result = JSON.parse(response)
			data = result["data"]

			return data
		rescue => e
			puts e.inspect
		end
	end

	def chart_data(country_array)
		chart_data_array = Array.new

		all = country_array.inject(Hash.new(0)) { |h, e| h[e] += 1 ; h }

		all.each do |country|
			array_pts = Array.new
			array_pts.push(country[0])
			array_pts.push(country[1])

			chart_data_array.push(array_pts)
		end

		return chart_data_array

    end
end
