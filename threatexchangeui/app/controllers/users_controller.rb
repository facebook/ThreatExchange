class UsersController < ApplicationController
	def edit
		@user = current_user
	end

	def update
		@user = current_user

		@user.app_id = params[:user][:app_id]
		@user.app_secret = params[:user][:app_secret]

		if @user.save
			redirect_to home_path, notice: "Successfully update your profile information."
		else
			render :edit
		end
	end

	def show
		if params[:id].to_i > 0
			redirect_to home_path
		else
			@user = User.find(params[:id])

			@rentals = @user.rentals
		end
	end

	private
      def user_params
          params.require(:user).permit(:first_name, :last_name, :email, :password, :password_confirmation, :app_id, :app_secret)
      end
end
