class ApplicationController < ActionController::Base
  	# Prevent CSRF attacks by raising an exception.
  	# For APIs, you may want to use :null_session instead.
  	protect_from_forgery with: :exception

  	rescue_from CanCan::AccessDenied do |exception|
        if user_signed_in?
            redirect_to home_path, :alert => exception.message
        else
            redirect_to root_path(:next=> request.path)
        end
    end

    load_and_authorize_resource :unless => :devise_controller?

    before_action :authenticate_user!
    before_action :configure_permitted_parameters, if: :devise_controller?

    protected

    def configure_permitted_parameters
        devise_parameter_sanitizer.for(:sign_up) { |u| u.permit(:first_name, :last_name, :email, :password) }
    end

  	def after_sign_out_path_for(resource)
  		root_path
  	end

    def after_sign_in_path_for(resource)
        if params[:user].nil?
            home_path
        else
            params[:user]["next"] || home_path
        end
    end
end
