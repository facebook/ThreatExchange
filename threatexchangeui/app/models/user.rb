class User < ActiveRecord::Base
  	# Include default devise modules. Others available are:
  	# :confirmable, :lockable, :timeoutable and :omniauthable
  	devise :database_authenticatable, :registerable,
         :recoverable, :rememberable, :trackable, :validatable

	validates_uniqueness_of :email, :case_sensitive => false
    validates_presence_of :last_name
    validates_presence_of :first_name

	def full_name
        [first_name, last_name].compact.join(' ')
    end

    extend FriendlyId
    friendly_id :first_name, use: [:slugged, :finders]
end
