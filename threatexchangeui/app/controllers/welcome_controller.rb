class WelcomeController < ApplicationController
	skip_before_action :authenticate_user!, :only => [:terms]
	skip_load_and_authorize_resource

	def index
	end
end
